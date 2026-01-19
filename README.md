# nhp_tag_runs_tui

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

## About

A Python-powered terminal user interface (TUI) to update entities in Azure Table Storage.

Interactively review and update the run-stage label of model results files for scenarios developed by schemes in the New Hospital Programme (NHP).
The run-stage label identifies scenarios used in reporting by [nhp_output_reports](https://github.com/The-Strategy-Unit/nhp_output_reports) and elsewhere.

This is a safer and faster alternative to editing table entities manually.

> [!NOTE]
> This tool is a work in progress with no guarantees.


## Install

You can install the tool from the web using [uv](https://docs.astral.sh/uv/getting-started/installation/).

```powershell
uv tool install git+https://github.com/The-Strategy-Unit/nhp_tag_runs_tui.git
```

Or, for development purposes, you can clone the repo and install it locally in editable mdoe.

```powershell
git clone https://github.com/The-Strategy-Unit/nhp_tag_runs_tui.git
cd nhp_tag_runs_tui
uv pip install -e .
```

## Set up

Login to Azure with [the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).
Select the account where the table exists.

```powershell
az login
```

Then set two environment variables.
You can obtain the environment-variable values from a member of the Data Science team.

In Powershell, you can store these variables on a per-session basis.
The values provided here are for demonstration purposes.

```powershell
$env:AZURE_STORAGE_ACCOUNT_NAME = "demoaccount"
$env:TAGGED_RUNS_TABLE_NAME = "demotable"
```

Or you can store them persistently.

```powershell
setx AZURE_STORAGE_ACCOUNT_NAME "demoaccount"
setx TAGGED_RUNS_TABLE_NAME "demotable"
```

These are used to build the table endpoint in the form `https://demoaccount.table.core.windows.net/demotable`.

## Use

After setup, you can enter the interactive TUI.

```bash
tag-runs
```

To summarise, the tool will:

1. Ask for an NHP scheme code.
2. Present a list of scenarios for that scheme.
3. Let you choose one via keyboard interaction.
4. Let you choose a run-stage label.
5. Edit the table given your selections.

Use <kbd>Ctrl</kbd> + <kbd>C</kbd> to quit out of the tool.
