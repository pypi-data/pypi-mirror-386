# Quickstart Guide: UiPath LangChain Agents

## Introduction

This guide provides step-by-step instructions for setting up, creating, publishing, and running your first UiPath-LangChain Agent.

## Prerequisites

Before proceeding, ensure you have the following installed:

-   Python 3.10 or higher
-   `pip` or `uv` package manager
-   A UiPath Automation Cloud account with appropriate permissions
-   An Anthropic or OpenAI API key

/// info

1. **Anthropic** - Generate an Anthropic API key [here](https://console.anthropic.com/settings/keys).

2. **OpenAI** - Generate an OpenAI API key [here](https://platform.openai.com).
   ///

## Creating a New Project

We recommend using `uv` for package management. To create a new project:

//// tab | Linux, macOS, Windows Bash

<!-- termynal -->

```shell
> mkdir example
> cd example
```

////

//// tab | Windows PowerShell

<!-- termynal -->

```powershell
> New-Item -ItemType Directory -Path example
> Set-Location example
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
# For Windows PowerShell/ Windows CMD: .venv\Scripts\activate
# For Windows Bash: source .venv/Scripts/activate
> source .venv/bin/activate

# Install the langchain anthropic package
> uv add langchain-anthropic

# Install the uipath package
> uv add uipath-langchain

# Verify the uipath installation
> uipath -lv
uipath-langchain version 0.0.100
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

# Install the langchain anthropic package
> pip install langchain-anthropic

# Install the uipath package
> pip install uipath-langchain

# Verify the uipath installation
> uipath -lv
uipath-langchain version 0.0.100
```

////

## Create Your First UiPath Agent

Generate your first UiPath LangChain agent:

<!-- termynal -->

```shell
> uipath new my-agent
⠋ Creating new agent my-agent in current directory ...
✓  Created 'main.py' file.
✓  Created 'langgraph.json' file.
✓  Created 'pyproject.toml' file.
💡  Initialize project: uipath init
💡  Run agent: uipath run agent '{"topic": "UiPath"}'
```

This command creates the following files:

| File Name        | Description                                                                                                                      |
|------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `main.py`        | LangGraph agent code.                                                                                                            |
| `langgraph.json` | [LangGraph](https://langchain-ai.github.io/langgraph/concepts/application_structure/#file-structure) specific configuration file. |
| `pyproject.toml` | Project metadata and dependencies as per [PEP 518](https://peps.python.org/pep-0518/).                                           |


## Authenticate With UiPath

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

## Initialize Project

<!-- termynal -->

```shell
> uipath init
⠋ Initializing UiPath project ...
✓   Created '.env' file.
✓   Created 'agent.mermaid' file.
✓   Created 'uipath.json' file.
```

This command creates the following files:

| File Name        | Description                                                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `.env`           | Environment variables and secrets (this file will not be packed & published).                                                     |
| `uipath.json`    | Input/output JSON schemas and bindings.                                                                                           |
| `agent.mermaid`  | Graph visual representation.                                                                                                      |

## Set Up Environment Variables

Before running the agent, configure either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in the `.env` file:

//// tab | Open AI

```
OPENAI_API_KEY=sk-proj-......
```

////

//// tab | ANTHROPIC_API_KEY

```
ANTHROPIC_API_KEY=sk-ant-a.....
```

////

## Run The Agent Locally

Execute the agent with a sample input:

<!-- termynal -->

```shell
> uipath run agent '{"topic": "UiPath"}'
[2025-04-29 12:31:57,756][INFO] ((), {'topic': 'UiPath'})
[2025-04-29 12:32:07,689][INFO] ((), {'topic': 'UiPath', 'report': "..."})
```

This command runs your agent locally and displays the report in the standard output.

/// warning
Depending on the shell you are using, it may be necessary to escape the input json:

/// tab | Bash/ZSH/PowerShell
```console
uipath run agent '{"topic": "UiPath"}'
```
///

/// tab | Windows CMD
```console
uipath run agent "{""topic"": ""UiPath""}"
```
///

/// tab | Windows PowerShell
```console
uipath run agent '{\"topic\":\"uipath\"}'
```
///

///

/// attention

For a shell agnostic option, please refer to the next section.

///

### (Optional) Run The Agent with a json File as Input

The `run` command can also take a .json file as an input. You can create a file named `input.json` having the following content:

```json
{
  "topic": "UiPath"
}
```

Use this file as agent input:

```shell
> uipath run agent --file input.json
```

## Deploy the Agent to UiPath Automation Cloud

Follow these steps to publish and run your agent to UiPath Automation Cloud:

### (Optional) Customize the Package

Update author details in `pyproject.toml`:

```toml
authors = [{ name = "Your Name", email = "your.name@example.com" }]
```

### Package Your Project

<!-- termynal -->

```shell
> uipath pack
⠋ Packaging project ...
Name       : test
Version    : 0.1.0
Description: Add your description here
Authors    : Your Name
✓  Project successfully packaged.
```

### Publish To My Workspace

<!-- termynal -->

```shell
> uipath publish --my-workspace
⠙ Publishing most recent package: my-agent.0.0.1.nupkg ...
✓  Package published successfully!
⠦ Getting process information ...
🔗 Process configuration link: [LINK]
💡 Use the link above to configure any environment variables
```

/// info
Please note that a process will be auto-created only upon publishing to **my-workspace** package feed.
   ///

Set the environment variables using the provided link:

<picture data-light="../quick_start_images/cloud_env_var_light.png" data-dark="../quick_start_images/cloud_env_var_dark.png">
  <source
    media="(prefers-color-scheme: dark)"
    srcset="../quick_start_images/cloud_env_var_dark.png"
  />
  <img
    src="../quick_start_images/cloud_env_var_light.png"
  />
</picture>

## Invoke the Agent on UiPath Automation Cloud

<!-- termynal -->

```shell
> uipath invoke agent '{"topic": "UiPath"}'
⠴ Loading configuration ...
⠴ Starting job ...
✨ Job started successfully!
🔗 Monitor your job here: [LINK]
```

Use the provided link to monitor your job and view detailed traces.

<picture data-light="../quick_start_images/invoke_output_light.png" data-dark="../quick_start_images/invoke_output_dark.png">
  <source
    media="(prefers-color-scheme: dark)"
    srcset="../quick_start_images/invoke_output_dark.png"
  />
  <img
    src="../quick_start_images/invoke_output_light.png"
  />
</picture>

### (Optional) Invoke The Agent with a json File as Input

The `invoke` command operates similarly to the `run` command, allowing you to use the same .json file defined
in the [(Optional) Run the agent with a .json file as input](#optional-run-the-agent-with-a-json-file-as-input)
section, as agent input:

```shell
> uipath invoke agent --file input.json
```

## Next Steps

Congratulations! You have successfully set up, created, published, and run a UiPath LangChain Agent. 🚀

For more advanced agents and agent samples, please refer to our [samples section](https://github.com/UiPath/uipath-langchain-python/tree/main/samples) in GitHub.
