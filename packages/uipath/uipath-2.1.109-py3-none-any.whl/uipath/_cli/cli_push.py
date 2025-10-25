# type: ignore
import asyncio
import os
from typing import Any, AsyncIterator, Optional
from urllib.parse import urlparse

import click

from uipath.models.exceptions import EnrichedException

from ..telemetry import track
from ._push.sw_file_handler import FileOperationUpdate, SwFileHandler
from ._utils._console import ConsoleLogger
from ._utils._constants import (
    UIPATH_PROJECT_ID,
)
from ._utils._project_files import (
    ensure_config_file,
    get_project_config,
    validate_config,
)
from ._utils._uv_helpers import handle_uv_operations

console = ConsoleLogger()


def get_org_scoped_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    org_name, *_ = parsed.path.strip("/").split("/")

    org_scoped_url = f"{parsed.scheme}://{parsed.netloc}/{org_name}"
    return org_scoped_url


async def upload_source_files_to_project(
    project_id: str,
    settings: Optional[dict[str, Any]],
    directory: str,
    include_uv_lock: bool = True,
) -> AsyncIterator[FileOperationUpdate]:
    """Upload source files to UiPath project, yielding progress updates.

    This function handles the pushing of local files to the remote project:
    - Updates existing files that have changed
    - Uploads new files that don't exist remotely
    - Deletes remote files that no longer exist locally
    - Optionally includes the UV lock file

    Yields:
        FileOperationUpdate: Progress updates for each file operation

    Raises:
        ProjectPushError: If the push operation fails
    """
    sw_file_handler = SwFileHandler(
        project_id=project_id,
        directory=directory,
        include_uv_lock=include_uv_lock,
    )

    async for update in sw_file_handler.upload_source_files(settings):
        yield update

    await sw_file_handler.upload_coded_evals_files()


@click.command()
@click.argument(
    "root", type=click.Path(exists=True, file_okay=False, dir_okay=True), default="."
)
@click.option(
    "--nolock",
    is_flag=True,
    help="Skip running uv lock and exclude uv.lock from the package",
)
@track
def push(root: str, nolock: bool) -> None:
    """Push local project files to Studio Web Project.

    This command pushes the local project files to a UiPath Studio Web project.
    It ensures that the remote project structure matches the local files by:
    - Updating existing files that have changed
    - Uploading new files
    - Deleting remote files that no longer exist locally
    - Optionally managing the UV lock file

    Args:
        root: The root directory of the project
        nolock: Whether to skip UV lock operations and exclude uv.lock from push

    Environment Variables:
        UIPATH_PROJECT_ID: Required. The ID of the UiPath Cloud project

    Example:
        $ uipath push
        $ uipath push --nolock
    """
    ensure_config_file(root)
    config = get_project_config(root)
    validate_config(config)

    project_id = os.getenv(UIPATH_PROJECT_ID)
    if not project_id:
        console.error("UIPATH_PROJECT_ID environment variable not found.")

    async def push_with_updates():
        """Wrapper to handle async iteration and display updates."""
        async for update in upload_source_files_to_project(
            project_id,
            config.get("settings", {}),
            root,
            include_uv_lock=not nolock,
        ):
            console.info(update.message)

    with console.spinner("Pushing UiPath project to Studio Web..."):
        try:
            if not nolock:
                handle_uv_operations(root)

            asyncio.run(push_with_updates())

        except Exception as e:
            console.error(
                f"Failed to push UiPath project: {e}",
                include_traceback=not isinstance(e, EnrichedException),
            )
