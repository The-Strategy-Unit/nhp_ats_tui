# nhp_ats_tui

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Code quality](https://github.com/The-Strategy-Unit/nhp_ats_tui/actions/workflows/code-quality.yml/badge.svg)](https://github.com/The-Strategy-Unit/nhp_ats_tui/actions/workflows/code-quality.yml)

## About

### Purpose

A Python-powered terminal user interface (TUI) for Azure Table Storage (ATS).
Edit metadata for model runs developed by schemes in the New Hospital Programme (NHP).
This is a safer and faster alternative to editing tables manually.

This tool is intended for use by developers of the NHP model and not for wider public use.

### Extent

For now, the tool lets you review and update a model run's:

* run-stage property (`run_stage`), which flags scenarios for use by [nhp_output_reports](https://github.com/The-Strategy-Unit/nhp_output_reports) and other secondary products
* site properties (`sites_ip`, `sites_op` and`sites_aae`), which are used to filter results in [nhp_output_reports](https://github.com/The-Strategy-Unit/nhp_output_reports) (in development)

## Usage

### To develop

After cloning the repo, set two values in a `.env` file in the project directory:

* `AZURE_STORAGE_ACCOUNT_NAME`
* `MODEL_RUNS_TABLE_NAME`

They're used to build the table endpoint in the form `https://demoaccount.table.core.windows.net/demotable`.

Authorised users can obtain these values from the Data Science team.

### To install

Alternatively, you can install the tool from the web using [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv tool install git+https://github.com/The-Strategy-Unit/nhp_ats_tui.git
```

You can set the required environment variables in several ways.
You could:

* add a `.env` to the directory you're working in
* use e.g. `setx AZURE_STORAGE_ACCOUNT_NAME "demoaccount"` in Powershell (then restart the terminal) to set them persistently
* use `$env:AZURE_STORAGE_ACCOUNT_NAME = "demoaccount"` in Powershell to set them in the current session

### Login to Azure

Before using the tool, you must first login to Azure with [the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest):

```bash
az login
```

Assuming you're authorised, select the account where the table exists.

### Enter the TUI

Having completed the steps above, you can enter the interactive TUI:

```bash
edit-runs
```

Use your keyboard to navigate and provide input.

You can force-quit out of the tool with <kbd>Ctrl</kbd> + <kbd>C</kbd>.
