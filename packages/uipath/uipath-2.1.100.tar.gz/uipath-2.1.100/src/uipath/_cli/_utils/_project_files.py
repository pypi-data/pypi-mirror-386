# type: ignore
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, Tuple

from pydantic import BaseModel, TypeAdapter

from .._utils._console import ConsoleLogger
from ..models.runtime_schema import RuntimeSchema
from ._constants import is_binary_file
from ._studio_project import (
    ProjectFile,
    ProjectFolder,
    StudioClient,
    get_folder_by_name,
)

try:
    import tomllib
except ImportError:
    import tomli as tomllib
logger = logging.getLogger(__name__)


class FileConflictHandler(Protocol):
    """Protocol for handling file conflicts."""

    def should_overwrite(
        self, file_path: str, local_hash: str, remote_hash: str
    ) -> bool:
        """Return True to overwrite, False to skip."""
        ...


class AlwaysOverwriteHandler:
    """Handler that always overwrites files."""

    def should_overwrite(
        self, file_path: str, local_hash: str, remote_hash: str
    ) -> bool:
        return True


class AlwaysSkipHandler:
    """Handler that always skips conflicts."""

    def should_overwrite(
        self, file_path: str, local_hash: str, remote_hash: str
    ) -> bool:
        return False


class FileInfo(BaseModel):
    """Information about a file to be included in the project.

    Attributes:
        file_path: The absolute path to the file
        relative_path: The path relative to the project root
        is_binary: Whether the file should be treated as binary
    """

    file_name: str
    file_path: str
    relative_path: str
    is_binary: bool


console = ConsoleLogger()


def get_project_config(directory: str) -> dict[str, str]:
    """Retrieve and combine project configuration from uipath.json and pyproject.toml.

    Args:
        directory: The root directory containing the configuration files

    Returns:
        dict[str, str]: Combined configuration including project name, description,
            entry points, version, and authors

    Raises:
        SystemExit: If required configuration files are missing or invalid
    """
    config_path = os.path.join(directory, "uipath.json")
    toml_path = os.path.join(directory, "pyproject.toml")

    if not os.path.isfile(config_path):
        console.error("uipath.json not found, please run `uipath init`.")
    if not os.path.isfile(toml_path):
        console.error("pyproject.toml not found.")

    with open(config_path, "r") as config_file:
        config_data = TypeAdapter(RuntimeSchema).validate_python(json.load(config_file))

    toml_data = read_toml_project(toml_path)

    return {
        "project_name": toml_data["name"],
        "description": toml_data["description"],
        "entryPoints": [ep.model_dump(by_alias=True) for ep in config_data.entrypoints],
        "version": toml_data["version"],
        "authors": toml_data["authors"],
        "dependencies": toml_data.get("dependencies", {}),
        "requires-python": toml_data.get("requires-python", None),
        "settings": config_data.settings or {},
    }


def validate_config(config: dict[str, str]) -> None:
    """Validate the combined project configuration.

    Checks for required fields and invalid characters in project name and description.

    Args:
        config: The combined configuration dictionary from uipath.json and pyproject.toml

    Raises:
        SystemExit: If validation fails for any required field or contains invalid characters
    """
    if not config["project_name"] or config["project_name"].strip() == "":
        console.error(
            "Project name cannot be empty. Please specify a name in pyproject.toml."
        )

    if not config["description"] or config["description"].strip() == "":
        console.error(
            "Project description cannot be empty. Please specify a description in pyproject.toml."
        )

    if not config["authors"] or config["authors"].strip() == "":
        console.error(
            'Project authors cannot be empty. Please specify authors in pyproject.toml:\n    authors = [{ name = "John Doe" }]'
        )

    if not config["requires-python"] or config["requires-python"].strip() == "":
        console.error(
            "'requires-python' field cannot be empty. Please specify it in pyproject.toml:  requires-python = \">=3.10\""
        )

    invalid_chars = ["&", "<", ">", '"', "'", ";"]
    for char in invalid_chars:
        if char in config["description"]:
            console.error(f"Project description contains invalid character: '{char}'")

    invalid_chars += [" "]
    for char in invalid_chars:
        if char in config["project_name"]:
            console.error(f"Project name contains invalid character: '{char}'")


def validate_config_structure(config_data: dict[str, Any]) -> None:
    """Validate the structure of uipath.json configuration.

    Args:
        config_data: The raw configuration data from uipath.json

    Raises:
        SystemExit: If required fields are missing from the configuration
    """
    required_fields = ["entryPoints"]
    for field in required_fields:
        if field not in config_data:
            console.error(f"uipath.json is missing the required field: {field}.")


def ensure_config_file(directory: str) -> None:
    """Check if uipath.json exists in the specified directory.

    Args:
        directory: The directory to check for uipath.json

    Raises:
        SystemExit: If uipath.json is not found in the directory
    """
    if not os.path.isfile(os.path.join(directory, "uipath.json")):
        console.error(
            "uipath.json not found. Please run `uipath init` in the project directory."
        )


def extract_dependencies_from_toml(project_data: Dict) -> Dict[str, str]:
    """Extract and parse dependencies from pyproject.toml project data.

    Args:
        project_data: The "project" section from pyproject.toml

    Returns:
        Dictionary mapping package names to version specifiers
    """
    dependencies = {}

    if "dependencies" not in project_data:
        return dependencies

    deps_list = project_data["dependencies"]
    if not isinstance(deps_list, list):
        console.warning("dependencies should be a list in pyproject.toml")
        return dependencies

    for dep in deps_list:
        if not isinstance(dep, str):
            console.warning(f"Skipping non-string dependency: {dep}")
            continue

        try:
            name, version_spec = parse_dependency_string(dep)
            if name:  # Only add if we got a valid name
                dependencies[name] = version_spec
        except Exception as e:
            console.warning(f"Failed to parse dependency '{dep}': {e}")
            continue

    return dependencies


def parse_dependency_string(dependency: str) -> Tuple[str, str]:
    """Parse a dependency string into package name and version specifier.

    Handles PEP 508 dependency specifications including:
    - Simple names: "requests"
    - Version specifiers: "requests>=2.28.0"
    - Complex specifiers: "requests>=2.28.0,<3.0.0"
    - Extras: "requests[security]>=2.28.0"
    - Environment markers: "requests>=2.28.0; python_version>='3.8'"

    Args:
        dependency: Raw dependency string from pyproject.toml

    Returns:
        Tuple of (package_name, version_specifier)

    Examples:
        "requests" -> ("requests", "*")
        "requests>=2.28.0" -> ("requests", ">=2.28.0")
        "requests>=2.28.0,<3.0.0" -> ("requests", ">=2.28.0,<3.0.0")
        "requests[security]>=2.28.0" -> ("requests", ">=2.28.0")
    """
    # Remove whitespace
    dependency = dependency.strip()

    # Handle environment markers (everything after semicolon)
    if ";" in dependency:
        dependency = dependency.split(";")[0].strip()

    # Pattern to match package name with optional extras and version specifiers
    # Matches: package_name[extras] version_specs
    pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)(\[[^\]]+\])?(.*)"
    match = re.match(pattern, dependency)

    if not match:
        # Fallback for edge cases
        return dependency, "*"

    package_name = match.group(1)
    version_part = match.group(4).strip() if match.group(4) else ""

    # If no version specifier, return wildcard
    if not version_part:
        return package_name, "*"

    # Clean up version specifier
    version_spec = version_part.strip()

    # Validate that version specifier starts with a valid operator
    valid_operators = [">=", "<=", "==", "!=", "~=", ">", "<"]
    if not any(version_spec.startswith(op) for op in valid_operators):
        # If it doesn't start with an operator, treat as exact version
        if version_spec:
            version_spec = f"=={version_spec}"
        else:
            version_spec = "*"

    return package_name, version_spec


def read_toml_project(file_path: str) -> dict:
    """Read and parse pyproject.toml file with improved error handling and validation.

    Args:
        file_path: Path to pyproject.toml file

    Returns:
        Dictionary containing project metadata and dependencies
    """
    try:
        with open(file_path, "rb") as f:
            content = tomllib.load(f)
    except Exception as e:
        console.error(f"Failed to read or parse pyproject.toml: {e}")

    # Validate required sections
    if "project" not in content:
        console.error("pyproject.toml is missing the required field: project.")

    project = content["project"]

    # Validate required fields with better error messages
    required_fields = {
        "name": "Project name is required in pyproject.toml",
        "description": "Project description is required in pyproject.toml",
        "version": "Project version is required in pyproject.toml",
    }

    for field, error_msg in required_fields.items():
        if field not in project:
            console.error(
                f"pyproject.toml is missing the required field: project.{field}. {error_msg}"
            )

        # Check for empty values only if field exists
        if field in project and (
            not project[field]
            or (isinstance(project[field], str) and not project[field].strip())
        ):
            console.error(
                f"Project {field} cannot be empty. Please specify a {field} in pyproject.toml."
            )

    # Extract author information safely
    authors = project.get("authors", [])
    author_name = ""

    if authors and isinstance(authors, list) and len(authors) > 0:
        first_author = authors[0]
        if isinstance(first_author, dict):
            author_name = first_author.get("name", "")
        elif isinstance(first_author, str):
            # Handle case where authors is a list of strings
            author_name = first_author

    # Extract dependencies with improved parsing
    dependencies = extract_dependencies_from_toml(project)

    return {
        "name": project["name"].strip(),
        "description": project["description"].strip(),
        "version": project["version"].strip(),
        "authors": author_name.strip(),
        "dependencies": dependencies,
        "requires-python": project.get("requires-python", "").strip(),
    }


def files_to_include(
    settings: Optional[dict[str, Any]],
    directory: str,
    include_uv_lock: bool = True,
    directories_to_ignore: list[str] | None = None,
) -> list[FileInfo]:
    """Get list of files to include in the project based on configuration.

    Walks through the directory tree and identifies files to include based on extensions
    and explicit inclusion rules. Skips virtual environments and hidden directories.

    Args:
        settings: File handling settings
        directory: Root directory to search for files
        include_uv_lock: Whether to include uv.lock file
        directories_to_ignore: List of directories to ignore

    Returns:
        list[FileInfo]: List of file information objects for included files
    """
    file_extensions_included = [".py", ".mermaid", ".json", ".yaml", ".yml", ".md"]
    files_included = ["pyproject.toml"]
    files_excluded = []

    if directories_to_ignore is None:
        directories_to_ignore = []
    if include_uv_lock:
        files_included += ["uv.lock"]
    if settings is not None:
        if "fileExtensionsIncluded" in settings:
            file_extensions_included.extend(settings["fileExtensionsIncluded"])
        if "filesIncluded" in settings:
            files_included.extend(settings["filesIncluded"])
        if "filesExcluded" in settings:
            files_excluded.extend(settings["filesExcluded"])
        if "directoriesExcluded" in settings:
            directories_to_ignore.extend(settings["directoriesExcluded"])

    def is_venv_dir(d: str) -> bool:
        """Check if a directory is a Python virtual environment.

        Args:
            d: Directory path to check

        Returns:
            bool: True if directory is a virtual environment, False otherwise
        """
        return (
            os.path.exists(os.path.join(d, "Scripts", "activate"))
            if os.name == "nt"
            else os.path.exists(os.path.join(d, "bin", "activate"))
        )

    extra_files: list[FileInfo] = []
    # Walk through directory and return all files in the allowlist
    for root, dirs, files in os.walk(directory):
        # Skip all directories that start with . or are a venv or are excluded
        included_dirs = []
        for d in dirs:
            if d.startswith(".") or is_venv_dir(os.path.join(root, d)):
                continue

            # Check if directory should be excluded
            dir_path = os.path.join(root, d)
            dir_rel_path = os.path.relpath(dir_path, directory)
            normalized_dir_rel_path = dir_rel_path.replace(os.sep, "/")

            # Check exclusion: by dirname (for root level) or by relative path
            should_exclude_dir = (
                (
                    (
                        d in directories_to_ignore and normalized_dir_rel_path == d
                    )  # name match for root level only
                    or normalized_dir_rel_path
                    in directories_to_ignore  # path match for nested directories
                )
                if directories_to_ignore is not None
                else False
            )

            if not should_exclude_dir:
                included_dirs.append(d)

        dirs[:] = included_dirs
        for file in files:
            file_extension = os.path.splitext(file)[1].lower()
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            rel_path = os.path.relpath(file_path, directory)

            # Normalize the path
            normalized_rel_path = rel_path.replace(os.sep, "/")

            # Check inclusion: by extension, by filename (for base directory), or by relative path
            should_include = (
                file_extension in file_extensions_included
                or (
                    file in files_included and normalized_rel_path == file
                )  # filename match for base directory only
                or normalized_rel_path
                in files_included  # path match for subdirectories
            )

            # Check exclusion: by filename (for base directory only) or by relative path
            should_exclude = (
                (
                    file in files_excluded and normalized_rel_path == file
                )  # filename match for base directory only
                or normalized_rel_path
                in files_excluded  # path match for subdirectories
            )

            if should_include and not should_exclude:
                extra_files.append(
                    FileInfo(
                        file_name=file_name,
                        file_path=file_path,
                        relative_path=rel_path,
                        is_binary=is_binary_file(file_extension),
                    )
                )
    return extra_files


def compute_normalized_hash(content: str) -> str:
    """Compute hash of normalized content.

    Args:
        content: Content to hash

    Returns:
        str: SHA256 hash of the normalized content
    """
    try:
        # Try to parse as JSON to handle formatting
        json_content = json.loads(content)
        normalized = json.dumps(json_content, indent=2)
    except json.JSONDecodeError:
        # Not JSON, normalize line endings
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def collect_files_from_folder(
    folder: ProjectFolder, base_path: str, files_dict: Dict[str, ProjectFile]
) -> None:
    """Recursively collect all files from a folder and its subfolders.

    Args:
        folder: The folder to collect files from
        base_path: Base path for file paths
        files_dict: Dictionary to store collected files
    """
    # Add files from current folder
    for file in folder.files:
        file_path = os.path.join(base_path, file.name)
        files_dict[file_path] = file

    # Recursively process subfolders
    for subfolder in folder.folders:
        subfolder_path = os.path.join(base_path, subfolder.name)
        collect_files_from_folder(subfolder, subfolder_path, files_dict)


async def pull_project(
    project_id: str,
    download_configuration: dict[str, Path],
    conflict_handler: Optional[FileConflictHandler] = None,
):
    """Pull project with configurable conflict handling."""
    if conflict_handler is None:
        conflict_handler = AlwaysOverwriteHandler()

    studio_client = StudioClient(project_id)

    try:
        structure = await studio_client.get_project_structure_async()
        for source_key, destination in download_configuration.items():
            source_folder = get_folder_by_name(structure, source_key)
            if source_folder:
                await download_folder_files(
                    studio_client, source_folder, destination, conflict_handler
                )
            else:
                logger.warning(f"No '{source_key}' folder found in remote project")
    except Exception:
        logger.exception("Failed to pull UiPath project")
        raise


async def download_folder_files(
    studio_client: StudioClient,
    folder: ProjectFolder,
    base_path: Path,
    conflict_handler: FileConflictHandler,
) -> None:
    """Download files from a folder recursively.

    Args:
        studio_client: Studio client
        folder: The folder to download files from
        base_path: Base path for local file storage
        conflict_handler: Handler for file conflicts
    """
    files_dict: Dict[str, ProjectFile] = {}
    collect_files_from_folder(folder, "", files_dict)

    for file_path, remote_file in files_dict.items():
        local_path = base_path / file_path
        local_path.parent.mkdir(parents=True, exist_ok=True)

        response = await studio_client.download_project_file_async(remote_file)
        remote_content = response.read().decode("utf-8")
        remote_hash = compute_normalized_hash(remote_content)

        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                local_content = f.read()
                local_hash = compute_normalized_hash(local_content)

            if local_hash != remote_hash:
                if conflict_handler.should_overwrite(
                    file_path, local_hash, remote_hash
                ):
                    with open(local_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write(remote_content)
                    logger.info(f"Updated '{file_path}'")
                else:
                    logger.info(f"Skipped '{file_path}'")
            else:
                logger.info(f"File '{file_path}' is up to date")
        else:
            with open(local_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(remote_content)
            logger.info(f"Downloaded '{file_path}'")
