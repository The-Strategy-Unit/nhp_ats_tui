"""
TUI for editing NHP model-run entities in Azure Table Storage.
"""

import os
from InquirerPy import inquirer

from .table import (
    get_table_client,
    get_unique_schemes,
    fetch_scenarios,
    list_scenarios,
    update_entity,
)


def main() -> None:
    """
    Run the interactive editing session.
    """
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    table_name = os.getenv("TAGGED_RUNS_TABLE_NAME")
    print("⏳ Connecting to table...")
    table = get_table_client(storage_account_name, table_name)

    print("⌛ Fetching scheme codes...")
    schemes_unique = get_unique_schemes(table)
    scheme_choice = inquirer.fuzzy(
        message="Start typing a scheme code and choose from filtered results:",
        choices=schemes_unique,
    ).execute()

    scenarios = fetch_scenarios(table, scheme_choice)
    scenarios_list = list_scenarios(scenarios)
    scenario_choice = inquirer.select(
        message="Choose a scenario to tag:",
        choices=scenarios_list,
    ).execute()

    tag_choice = inquirer.select(
        message="Choose a run-stage tag:",
        choices=[
            "final_report_ndg2",
            "final_report_ndg3",
            "validation_report_ndg2",
            "validation_report_ndg3",
        ],
    ).execute()

    update_entity(table, scheme_choice, scenario_choice, tag_choice)

    print(f"✅ Updated {scenario_choice} for scheme {scheme_choice}.")
    print(f"🏷️  Set run_stage tag to '{tag_choice}'.")


if __name__ == "__main__":
    main()
