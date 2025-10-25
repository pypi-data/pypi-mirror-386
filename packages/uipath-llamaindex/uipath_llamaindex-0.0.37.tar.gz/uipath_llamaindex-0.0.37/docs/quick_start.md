# Quickstart Guide: UiPath LlamaIndex Agents

## Introduction

This guide provides step-by-step instructions for setting up, creating, publishing, and running your first UiPath-LlamaIndex Agent.

## Prerequisites

Before proceeding, ensure you have the following installed:

-   Python 3.10 or higher
-   `pip` or `uv` package manager
-   A UiPath Automation Cloud account with appropriate permissions
-   An OpenAI API key

/// info
 **OpenAI** - Generate an OpenAI API key [here](https://platform.openai.com).
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

# Install the uipath package
> uv add uipath-llamaindex
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
> pip install uipath-llamaindex
```

////

## Create Your First UiPath Agent

Generate your first UiPath LlamaIndex agent:

<!-- termynal -->

```shell
> uipath new my-agent
⠋ Creating new agent my-agent in current directory ...
✓  Created 'main.py' file.
✓  Created 'llama_index.json' file.
✓  Created 'pyproject.toml' file.
🔧  Please ensure to define OPENAI_API_KEY in your .env file.
💡  Initialize project: uipath init
💡  Run agent: uipath run agent '{"topic": "UiPath"}'
```

This command creates the following files:

| File Name        | Description                                                                                                                      |
|------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `main.py`        | LlamaIndex agent code.                                                                                                            |
| `llama_index.json` | LlamaIndex specific configuration file. |
| `pyproject.toml` | Project metadata and dependencies as per [PEP 518](https://peps.python.org/pep-0518/).                                           |


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

Before running the agent, configure `OPENAI_API_KEY` in the `.env` file:

//// tab | Open AI

```
OPENAI_API_KEY=sk-proj-......
```

////

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

## Run The Agent Locally

Execute the agent with a sample input:

<!-- termynal -->

```shell
> uipath run agent '{"topic": "UiPath"}'
{'joke': 'Why did the UiPath robot go to therapy? \nBecause it had too many unresolved workflows!', 'critique': "Analysis:\nThis joke plays on the concept of therapy and unresolved issues, but applies it to a UiPath robot, which is a software automation tool used in businesses. The joke cleverly incorporates the idea of workflows, which are sequences of automated tasks that the robot performs, as the source of the robot's need for therapy.\n\nCritique:\n- Clever wordplay: The joke is clever in its use of wordplay, as it takes a common phrase related to therapy and applies it in a humorous way to a robot and its workflows. This adds an element of surprise and wit to the joke.\n- Relevant to the audience: The joke is likely to resonate with those familiar with UiPath or other automation tools, as they will understand the reference to workflows and the challenges that can arise from managing them.\n- Lack of depth: While the joke is amusing on the surface, it may lack depth or complexity compared to more nuanced humor. Some may find it to be a simple play on words rather than a joke with deeper layers of meaning.\n- Limited appeal: The joke's humor may be limited to a specific audience who are familiar with automation tools and workflows, potentially excluding those who are not familiar with these concepts.\n\nOverall, the joke is a clever play on words that will likely resonate with those in the automation industry, but may not have broad appeal beyond that specific audience."}
✓  Successful execution.
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

Congratulations! You have successfully set up, created, published, and run a UiPath LlamaIndex Agent. 🚀

For more advanced agents and agent samples, please refer to our [samples section](https://github.com/UiPath/uipath-llamaindex-python/tree/main/samples) in GitHub.
