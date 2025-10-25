# Getting Started

## Prerequisites

-   Python 3.10 or higher
-   `pip` or `uv` package manager
-   A UiPath Cloud Platform account with appropriate permissions

## Getting Started with the CLI

//// tab | Linux, macOS, Windows Bash

<!-- termynal -->

```shell
> mkdir uipath_coded_process
> cd uipath_coded_process
```

////

//// tab | Windows PowerShell

<!-- termynal -->

```powershell
> New-Item -ItemType Directory -Path uipath_coded_process
> Set-Location uipath_coded_process
```

////

//// tab | uv
    new: true

<!-- termynal -->

```shell
# Initialize a new uv project in the current directory
> uv init . --python 3.10

# Create a new virtual environment
# By default, uv creates a virtual environment in a directory called .venv
> uv venv
Using CPython 3.10.16 interpreter at: [PATH]
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

# Activate the virtual environment
# For Windows PowerShell: .venv\Scripts\Activate.ps1
# For Windows Bash: source .venv/Scripts/activate
> source .venv/bin/activate

# Install the uipath package
> uv add uipath

# Verify the uipath installation
> uipath --version
uipath version 2.0.29
```

////

//// tab | pip

<!-- termynal -->

```shell
# Create a new virtual environment
> python -m venv .venv

# Activate the virtual environment
# For Windows PowerShell: .venv\Scripts\Activate.ps1
# For Windows Bash: source .venv/Scripts/activate
> source .venv/bin/activate

# Upgrade pip to the latest version
> python -m pip install --upgrade pip

# Install the uipath package
> pip install uipath

# Verify the uipath installation
> uipath --version
uipath version 2.0.29
```

////

### Telemetry

To help us improve the developer experience, the CLI collects basic usage data about commands invocation. For more details about UiPath’s privacy practices, please review the [privacy statement](https://www.uipath.com/legal/privacy-policy).

#### Disabling telemetry data

Telemetry is enabled by default, yet it is possible to opt-out by setting to `false` the `UIPATH_TELEMETRY_ENABLED` environment variable.

### Authentication

To debug your script locally and publish your project, you need to authenticate with UiPath:

<!-- termynal -->

```shell
> uipath auth
⠋ Authenticating with UiPath ...
🔗 If a browser window did not open, please open the following URL in your browser: [LINK]
👇 Select tenant:
  0: Tenant1
  1: Tenant2
Select tenant number: 0
Selected tenant: Tenant1
✓  Authentication successful.
```

This command opens a new browser window for authentication. If you encounter any issues, copy the URL from the terminal and paste it into your browser. After authentication, select your tenant by entering its corresponding number in the terminal.

Upon successful authentication, your project will contain a `.env` file with your access token, UiPath URL, and other configuration details.

### Writing Your Code

Open `main.py` in your code editor. You can start with this example code:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class EchoIn:
    message: str
    repeat: Optional[int] = 1
    prefix: Optional[str] = None


@dataclass
class EchoOut:
    message: str


def main(input: EchoIn) -> EchoOut:
    result = []
    for _ in range(input.repeat or 1):
        line = input.message
        if input.prefix:
            line = f"{input.prefix}: {line}"
        result.append(line)

    return EchoOut(message="\n".join(result))
```

### Initializing the UiPath Project

To create a UiPath project, run the following command in your terminal:

<!-- termynal -->

```shell
> uipath init
⠋ Initializing UiPath project ...
✓  Created 'uipath.json' file.
```

/// warning

The `uipath init` command executes your `main.py` file to analyze its structure and collect information about inputs and outputs.
///

This command creates a `uipath.json` file containing the project metadata.

<!-- termynal -->

```shell
# Debug your project
> uipath run main.py '{"message": "test"}'
[2025-04-11 10:13:58,857][INFO] {'message': 'test'}
```

/// warning
Depending on the shell you are using, it may be necessary to escape the input json:

/// tab | Bash/ZSH/PowerShell
```console
uipath run main.py '{"message": "test"}'
```
///

/// tab | Windows CMD
```console
uipath run main.py "{""message"": ""test""}"
```
///

/// tab | Windows PowerShell
```console
uipath run main.py '{\"message\":\"test\"}'
```
///

///

### Packaging and Publishing

Before packaging your project, add your details to the `pyproject.toml` file. Add the following line below the `description` field:

```toml
authors = [{ name = "Your Name", email = "your.email@uipath.com" }]
```

Then, package your project:

<!-- termynal -->

```shell
> uipath pack
⠋ Packaging project ...
Name       : uipath_coded_process
Version    : 0.1.0
Description: Add your description here
Authors    : Your Name
✓  Project successfully packaged.
```

Finally, publish your package:

<!-- termynal -->

```shell
> uipath publish
⠋ Fetching available package feeds...
👇 Select package feed:
  0: Orchestrator Tenant Processes Feed
  1: Orchestrator Personal Workspace Feed
Select feed number: 0
Selected feed: Orchestrator Tenant Processes Feed
⠸ Publishing most recent package: uipath_coded_process.0.1.0.nupkg ...
✓  Package published successfully!
```

After selecting your publishing destination (tenant or personal workspace), you'll see details about your package and a confirmation message.

## Integrating with the UiPath Platform

Create a **new project** (separate from the one you just packaged and published) following the same steps as above. This new project will invoke your previous process using the UiPath SDK.

Open `main.py` in your code editor and add the following code:

```python
from uipath import UiPath


def main():
    sdk = UiPath()
    sdk.processes.invoke(
        "uipath_coded_process",
        input_arguments={
            "message": "Hello, World!",
            "repeat": 3,
            "prefix": "[Echo]"
        },
        folder_path="PROCESS_FOLDER_PATH_HERE"
    )
```

/// warning
An agent can invoke itself if needed, but this must be done with caution. Be mindful that using the same name for invocation may lead to unintentional loops. To prevent recursion issues, implement safeguards like exit conditions.
///

### Verifying the Execution

<!-- termynal -->

```shell
> uipath run main.py
```

Open your browser and navigate to UiPath. Go to the specified folder, where you'll see a new job for `uipath_coded_process` has been executed. The output will be:

```
[Echo]: Hello, World! Echo: Hello, World! Echo: Hello, World!
```
