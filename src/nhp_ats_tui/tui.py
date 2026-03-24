"""
TUI for editing NHP model-run entities in Azure Table Storage.
"""

import os
from InquirerPy import inquirer
from dotenv import load_dotenv

from .table import (
    get_table_client,
    get_unique_schemes,
    fetch_scenarios,
    list_scenarios,
    update_run_stage,
    update_sites,
)


def main() -> None:
    """
    Run the interactive editing session.
    """
    load_dotenv()
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    table_name = os.getenv("MODEL_RUNS_TABLE_NAME")
    print("⏳ Connecting to table...")
    table = get_table_client(storage_account_name, table_name)

    print("⌛ Fetching scheme codes...")
    schemes_unique = get_unique_schemes(table)
    scheme_choice = inquirer.fuzzy(
        message="Choose a scheme:",
        choices=schemes_unique,
    ).execute()

    scenarios = fetch_scenarios(table, scheme_choice)
    scenarios_list = list_scenarios(scenarios)

    scenario_choice = inquirer.select(
        message="Choose a scenario to edit:",
        choices=scenarios_list,
    ).execute()

    task_choice = inquirer.select(
        message="Choose a task",
        choices=[
            "Edit the run stage",
            "Edit sites (inpatients)",
            "Edit sites (outpatients)",
            "Edit sites (A&E)",
        ],
    ).execute()

    if task_choice == "Edit the run stage":
        tag_choice = inquirer.select(
            message="Choose a run-stage tag:",
            choices=[
                "final_report_ndg2",
                "final_report_ndg3",
                "validation_report_ndg2",
                "validation_report_ndg3",
            ],
        ).execute()

        update_run_stage(table, scheme_choice, scenario_choice, tag_choice)

        print(f"🏷️  Set run_stage tag to '{tag_choice}'.")

    elif "Edit sites" in task_choice:
        print("Current sites: TODO")

        if "inpatients" in task_choice:
            activity_type_choice = "inpatients"
        elif "outpatients" in task_choice:
            activity_type_choice = "outpatients"
        elif "A&E" in task_choice:
            activity_type_choice = "A&E"

        sites_provided = (
            inquirer.text(
                "Provide sites (like 'XYZ01,XYZ02' or 'ALL' or blank to remove):"
            ).execute()
            or ""
        )

        update_sites(
            table,
            scheme_choice,
            scenario_choice,
            activity_type_choice,
            sites_provided,  # gets deleted if empty string
        )

        if sites_provided == "":
            print(f"🏥 Removed all {activity_type_choice} sites.")
        else:
            print(f"🏥 Set {activity_type_choice} sites to '{sites_provided}'.")

    print(f"✅ Updated {scenario_choice} for scheme {scheme_choice}. Exiting.")


if __name__ == "__main__":
    main()
