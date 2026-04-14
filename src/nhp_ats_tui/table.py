"""
Access and handle entities from Azure Table Storage.
"""

from azure.data.tables import TableClient, TableEntity, UpdateMode
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


def get_table_entity(
    table: TableClient,
    scheme_choice: str,
    scenario_choice: str,
) -> TableEntity:
    """
    Get a TableEntity from an authenticated TableClient instance.

    Args:
        table (TableClient): An authenticated TableClient.
        scheme_choice (str): Selected scheme code (the entity's PartitionKey).
        scenario_choice (str): Selected scenario name.

    Returns:
        A TableEntity.
    """

    scenario_choice_split = scenario_choice.split()
    scenario = scenario_choice_split[0]
    created = scenario_choice_split[1].strip("()")

    # RowKey is an entity-unique identifier, composed of name and datetime
    row_key = f"{scenario}-{created}"

    entity = table.get_entity(
        partition_key=scheme_choice,
        row_key=row_key,
    )

    return entity


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
    scheme_choice: str,
    scenario_choice: str,
    tag_choice: str | None,
) -> None:
    """
    Update the run-stage property for an existing scenario entity.

    Args:
        table_client (TableClient): An authenticated TableClient.
        scheme_choice (str): Selected scheme code (the entity's PartitionKey).
        scenario_choice (str): Selected scenario name.
        tag_choice (str | None): Selected run-stage tag.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    entity = get_table_entity(table_client, scheme_choice, scenario_choice)

    if tag_choice is None:
        entity.pop("run_stage", None)
    else:
        entity["run_stage"] = tag_choice

    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.REPLACE,  # REPLACE because properties may have been removed
    )


def update_sites(
    table_client: TableClient,
    scheme_choice: str,
    scenario_choice: str,
    activity_type_choice: str,
    sites_provided: str | None,
) -> None:
    """
    Update or remove the site-code property for an existing scenario entity.

    Args:
        table_client (TableClient): An authenticated TableClient.
        scheme_choice (str): Selected scheme code (the entity's PartitionKey).
        scenario_choice (str): Selected scenario name.
        activity_type_choice (str): Selected activity type.
        sites_provided (str | None): A comma-separated string of site codes.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    entity = get_table_entity(table_client, scheme_choice, scenario_choice)

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
