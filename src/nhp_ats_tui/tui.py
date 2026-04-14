"""
TUI for editing NHP model-run entities in Azure Table Storage.
"""

import os
from InquirerPy import inquirer
from dotenv import load_dotenv

from .table import (
    get_table_client,
    get_table_entity,
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
    print("⏳ Getting environment variables...")
    load_dotenv()  # load from .env file, otherwise from environment
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    table_name = os.getenv("MODEL_RUNS_TABLE_NAME")

    if not storage_account_name or not table_name:
        raise EnvironmentError(
            "AZURE_STORAGE_ACCOUNT_NAME and MODEL_RUNS_TABLE_NAME must be set."
        )

    print("⏳ Connecting to table...")
    table = get_table_client(storage_account_name, table_name)

    print("⏳ Fetching scheme codes...")
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

        print(f"✅ Set run_stage tag to '{tag_choice}'. Exiting.")

    elif "Edit sites" in task_choice:
        entity = get_table_entity(table, scheme_choice, scenario_choice)

        if "inpatients" in task_choice:
            activity_type_choice = "inpatients"
            sites_existing = entity.get("sites_ip") or "none"
        elif "outpatients" in task_choice:
            activity_type_choice = "outpatients"
            sites_existing = entity.get("sites_op") or "none"
        elif "A&E" in task_choice:
            activity_type_choice = "A&E"
            sites_existing = entity.get("sites_aae") or "none"

        print(f"ℹ️  Current {activity_type_choice} sites: {sites_existing}")

        sites_provided = inquirer.text(
            "Provide sites (e.g. 'XYZ01,XYZ02', 'ALL') or leave blank to remove:"
        ).execute()

        update_sites(
            table,
            scheme_choice,
            scenario_choice,
            activity_type_choice,
            sites_provided,  # site property deleted if None
        )

        if sites_provided == "":
            print(f"✅ Removed all {activity_type_choice} sites. Exiting.")
        else:
            print(
                f"✅ Set {activity_type_choice} sites to '{sites_provided}'. Exiting."
            )


if __name__ == "__main__":
    main()
