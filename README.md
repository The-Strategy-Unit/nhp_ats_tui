# nhp_ats_tui

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

## About

A Python-powered terminal user interface (TUI) for Azure Table Storage (ATS).
Edit metadata for model runs developed by schemes in the New Hospital Programme (NHP)

For now, you can review and update:

* the run-stage property (`run_stage`), which flags scenarios for use by [nhp_output_reports](https://github.com/The-Strategy-Unit/nhp_output_reports)
* the site properties (`sites_*`), which are used to filter results in [nhp_output_reports](https://github.com/The-Strategy-Unit/nhp_output_reports) (in development)

This is a safer and faster alternative to editing tables manually.

## Install

You can install the tool from the web using [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv tool install git+https://github.com/The-Strategy-Unit/nhp_ats_tui.git
```

## Prerequisites

First, you must login to Azure with [the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).
Select the account where the table exists.

```bash
az login
```

Then set two environment variables.
Authorised users can obtain these values from a member of the Data Science team.

In Powershell, you can store these variables on a per-session basis.
The values provided here are for demonstration purposes.

```bash
$env:AZURE_STORAGE_ACCOUNT_NAME = "demoaccount"
$env:TAGGED_RUNS_TABLE_NAME = "demotable"
```

Or you can store them persistently.

```bash
setx AZURE_STORAGE_ACCOUNT_NAME "demoaccount"
setx TAGGED_RUNS_TABLE_NAME "demotable"
```

These are used to build the table endpoint in the form `https://demoaccount.table.core.windows.net/demotable`.

## Enter the TUI

After setup, you can enter the interactive TUI and follow the instructions.

```bash
edit-runs
```

You can force-quit out of the tool with <kbd>Ctrl</kbd> + <kbd>C</kbd>.

## For developers

Developers can clone the repo and install the tool locally in editable mode.
The flow might look like this:

```bash
git clone https://github.com/The-Strategy-Unit/nhp_ats_tui.git
cd nhp_ats_tui
uv venv
.venv\Scripts\activate
uv sync
uv pip install -e .
az login
$env:AZURE_STORAGE_ACCOUNT_NAME = "demoaccount"
$env:TAGGED_RUNS_TABLE_NAME = "demotable"
edit-runs
```
