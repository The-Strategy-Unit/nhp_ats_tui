"""
Access and handle entities from Azure Table Storage.
"""

from datetime import datetime, timezone

from azure.data.tables import TableClient, UpdateMode
from azure.identity import DefaultAzureCredential


def get_table_client(storage_account_name: str, table_name: str) -> TableClient:
    """
    Create an authenticated Azure TableClient instance.

    Args:
        storage_account_name (str): Name of the Azure Storage account.
        table_name (str): Name of the Azure Table Storage table.

    Returns:
        An authenticated TableClient instance.
    """
    endpoint = f"https://{storage_account_name}.table.core.windows.net"
    credential = DefaultAzureCredential()  # provided by az login at command line

    table_client = TableClient(
        endpoint=endpoint,
        table_name=table_name,
        credential=credential,
    )

    return table_client


def get_unique_schemes(table: TableClient) -> list[str]:
    """
    Retrieve all distinct scheme codes (PartitionKey values) from a table.

    Args:
        table (TableClient): An authenticated TableClient.

    Returns:
        A sorted list of unique scheme codes.
    """
    schemes = table.query_entities(
        query_filter="",  # mandatory argument, blank to return all entities
        select=["PartitionKey"],  # entities are partitioned by scheme code
    )
    schemes_unique = sorted({scheme["PartitionKey"] for scheme in schemes})

    return schemes_unique


def fetch_scenarios(table: TableClient, scheme_code: str) -> list[dict]:
    """
    Fetch all scenarios for a given scheme code.

    Args:
        table (TableClient): An authenticated TableClient.
        scheme_code (str): Selected scheme code (the entity's PartitionKey).

    Returns:
        A list of dictionaries containing scenario metadata.
    """
    filter_expr = f"PartitionKey eq '{scheme_code}'"
    entities = table.query_entities(query_filter=filter_expr)  # server-side query

    scenarios = []
    for entity in entities:
        scenarios.append(
            {
                # Identifiers
                "PartitionKey": entity["PartitionKey"],
                "RowKey": entity["RowKey"],
                "scenario": entity["scenario"],
                "create_datetime": entity["create_datetime"],
                # Items to edit
                "run_stage": entity.get("run_stage"),
                "sites_ip": entity.get("sites_ip"),
                "sites_op": entity.get("sites_op"),
                "sites_aae": entity.get("sites_aae"),
            }
        )

    return scenarios


def list_scenarios(scenarios: list[dict]) -> list[str]:
    """
    Format scenarios for display in an interactive selection list.

    Args:
        scenarios (list[dict]): List of scenario dictionaries returned by fetch_scenarios().

    Returns:
        A list of formatted scenario labels for TUI selection, in the format
        "<scenario> (<create_datetime>)", possibly appended with "[<run_stage>]".
    """
    values = []
    for scenario in scenarios:
        scenario_name = scenario["scenario"]
        created = scenario["create_datetime"]
        if scenario["run_stage"] is None:
            stage = ""
        else:
            stage = f" [{scenario['run_stage']}]"
        label = f"{scenario_name} ({created}){stage}"
        values.append(label)

    return values


def update_run_stage(
    table_client: TableClient,
    scenarios: list[dict],
    scheme_choice: str,
    scenario_choice: str,
    tag_choice: str | None,
) -> None:
    """
    Update the run-stage property for an existing scenario entity.

    Args:
        table_client (TableClient): An authenticated TableClient.
        scenarios (list[dict]): Each dict contains selected values for an entity.
        scheme_choice (str): Selected scheme code (the entity's PartitionKey).
        scenario_choice (str): Selected scenario name.
        tag_choice (str | None): Selected run-stage tag.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    entity = get_scenario(scenarios, scheme_choice, scenario_choice)

    if tag_choice is None:
        entity.pop("run_stage", None)
    else:
        entity["run_stage"] = tag_choice

    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.REPLACE,  # REPLACE because properties may have been removed
    )


def get_scenario(
    scenarios: list[dict], scheme_choice: str, scenario_choice: str
) -> dict:
    scenario_choice_split = scenario_choice.split()

    scenario_name = scenario_choice_split[0]

    date = scenario_choice_split[1].strip("(")
    time = scenario_choice_split[2].strip(")")
    datetime_str = f"{date} {time}"
    created_dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S+00:00").replace(
        tzinfo=timezone.utc
    )

    scenario = next(
        s
        for s in scenarios
        if s["PartitionKey"] == scheme_choice
        and s["scenario"] == scenario_name
        and s["create_datetime"] == created_dt
    )

    return scenario


def get_existing_sites(
    scenarios: list[dict], scheme_choice: str, scenario_choice: str, task_choice: str
) -> tuple:
    scenario = get_scenario(scenarios, scheme_choice, scenario_choice)

    if "inpatients" in task_choice:
        activity_type_choice = "inpatients"
        sites_existing = scenario.get("sites_ip") or "none"
    elif "outpatients" in task_choice:
        activity_type_choice = "outpatients"
        sites_existing = scenario.get("sites_op") or "none"
    elif "A&E" in task_choice:
        activity_type_choice = "A&E"
        sites_existing = scenario.get("sites_aae") or "none"

    return activity_type_choice, sites_existing


def update_sites(
    table_client: TableClient,
    scenarios: list[dict],
    scheme_choice: str,
    scenario_choice: str,
    activity_type_choice: str,
    sites_provided: str | None,
) -> None:
    """
    Update or remove the site-code property for an existing scenario entity.

    Args:
        table_client (TableClient): An authenticated TableClient.
        scenarios (list[dict]): Each dict contains selected values for an entity.
        scheme_choice (str): Selected scheme code (the entity's PartitionKey).
        scenario_choice (str): Selected scenario name.
        activity_type_choice (str): Selected activity type.
        sites_provided (str | None): A comma-separated string of site codes.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    entity = get_scenario(scenarios, scheme_choice, scenario_choice)

    if "inpatients" in activity_type_choice:
        # Remove the property from the entity if empty, otherwise overwrite
        if sites_provided is None:
            entity.pop("sites_ip", None)
        else:
            entity["sites_ip"] = sites_provided

    if "outpatients" in activity_type_choice:
        if sites_provided is None:
            entity.pop("sites_op", None)
        else:
            entity["sites_op"] = sites_provided

    if "A&E" in activity_type_choice:
        if sites_provided is None:
            entity.pop("sites_aae", None)
        else:
            entity["sites_aae"] = sites_provided

    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.REPLACE,  # REPLACE because properties may have been removed
    )
