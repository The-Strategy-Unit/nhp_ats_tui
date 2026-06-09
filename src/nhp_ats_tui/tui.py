"""
TUI for editing NHP model-run entities in Azure Table Storage.
"""

import os

from dotenv import load_dotenv
from InquirerPy import inquirer

from .table import (
    create_scenario_label_lookup,
    create_table_client,
    fetch_entities,
    filter_entities_by_dataset,
    find_entity_by_label,
    find_entity_sites,
    list_unique_schemes,
    update_run_stage,
    update_sites,
)


def main() -> None:
    """
    Run the interactive editing session.
    """
    print("ℹ Use Ctrl+C to exit at any point.")

    print("ℹ Getting environment variables...")
    load_dotenv()  # load from .env file, otherwise from environment
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    table_name = os.getenv("MODEL_RUNS_TABLE_NAME")

    if not storage_account_name or not table_name:
        raise EnvironmentError(
            "AZURE_STORAGE_ACCOUNT_NAME and MODEL_RUNS_TABLE_NAME must be set."
        )

    print("ℹ Connecting to table...", end=" ")
    table = create_table_client(storage_account_name, table_name)
    print(f"'{table_name}'.")

    print("ℹ Collecting entities...", end=" ")
    entities = fetch_entities(table)
    print(f"n = {len(entities)}.")

    print("ℹ Fetching scheme codes...", end=" ")
    schemes_unique = list_unique_schemes(entities)
    print(f"n = {len(schemes_unique)}.")

    while True:
        try:
            scheme_choice = inquirer.fuzzy(
                message="Choose a scheme:",
                choices=schemes_unique,
            ).execute()

            # Limit to chosen dataset
            dataset_entities = filter_entities_by_dataset(entities, scheme_choice)
            scenarios_lookup = create_scenario_label_lookup(dataset_entities)

            scenario_choice = inquirer.fuzzy(
                message="Choose a scenario to edit:",
                choices=list(scenarios_lookup.keys()),
            ).execute()

            # Limit to chosen scenario
            entity = find_entity_by_label(entities, scenario_choice, scenarios_lookup)

            task_choice = inquirer.select(
                message="Choose a task:",
                choices=[
                    "Edit the run stage",
                    "Edit sites (inpatients)",
                    "Edit sites (outpatients)",
                    "Edit sites (A&E)",
                ],
            ).execute()

            if task_choice == "Edit the run stage":
                tag_subtask_choice = inquirer.select(
                    message="Choose a run-stage option:",
                    choices=["Add/change", "Remove"],
                ).execute()

                if tag_subtask_choice == "Remove":
                    # Will cause run_stage property to be removed
                    tag_choice = None

                if tag_subtask_choice == "Add/change":
                    tag_choice = inquirer.select(
                        message="Choose a run-stage tag:",
                        choices=[
                            "final_report_ndg2",
                            "final_report_ndg3",
                            "validation_report_ndg3",
                            "validation_report_ndg2",
                            "Other",
                        ],
                    ).execute()

                    if tag_choice == "Other":
                        tag_choice = inquirer.text(
                            "Type a run-stage tag (lowercase, underscore-separated, with NDG variant):"
                        ).execute()

                update_run_stage(table, entity, tag_choice)

                if tag_subtask_choice == "Remove":
                    print("✓ Removed run-stage tag.")
                    print("ℹ Returning to scheme selection. Use Ctrl+C to exit.")
                else:
                    print(f"✓ Set run-stage tag to '{tag_choice}'.")
                    print("ℹ Returning to scheme selection. Use Ctrl+C to exit.")

            elif "Edit sites" in task_choice:
                activity_type_choice, sites_existing = find_entity_sites(
                    entity, task_choice
                )
                print(f"ℹ Current {activity_type_choice} sites: {sites_existing}.")

                sites_provided = inquirer.text(
                    "Type site codes (e.g. 'XYZ01,XYZ02', 'ALL') or leave blank to remove:"
                ).execute()

                update_sites(
                    table,
                    entity,
                    activity_type_choice,
                    sites_provided,  # site property will be deleted if None
                )

                if sites_provided == "":
                    print(f"✓ Removed all {activity_type_choice} sites.")
                    print("ℹ Returning to scheme selection. Use Ctrl+C to exit.")
                else:
                    print(f"✓ Set {activity_type_choice} sites to '{sites_provided}'.")
                    print("ℹ Returning to scheme selection. Use Ctrl+C to exit.")

        except KeyboardInterrupt:
            print("✕ Interrupted. Exiting.")  # on Ctrl+C
            return


if __name__ == "__main__":
    main()
