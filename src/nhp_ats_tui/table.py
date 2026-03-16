"""
Access and handle entities from Azure Table Storage.
"""

from azure.data.tables import TableClient, UpdateMode
from azure.identity import DefaultAzureCredential


def get_table_client(storage_account_name: str, table_name: str) -> TableClient:
    """
    Create an authenticated Azure TableClient instance.

    Args:
        storage_account_name: Name of the Azure Storage account.
        table_name: Name of the Azure Table Storage table.

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
        table: An authenticated TableClient.

    Returns:
        A sorted list of unique scheme codes.
    """
    schemes = table.query_entities(
        query_filter=None,  # mandatory argument
        select=["PartitionKey"],  # entities are partitioned by scheme code
    )
    schemes_unique = sorted({scheme["PartitionKey"] for scheme in schemes})

    return schemes_unique


def fetch_scenarios(table: TableClient, scheme_code: str) -> list[dict]:
    """
    Fetch all scenarios for a given scheme code.

    Args:
        table: An authenticated TableClient.
        scheme_code: Scheme code (PartitionKey) value.

    Returns:
        A list of dictionaries containing scenario metadata.
    """
    filter_expr = f"PartitionKey eq '{scheme_code}'"
    entities = table.query_entities(query_filter=filter_expr)  # server-side query

    scenarios = []
    for entity in entities:
        scenarios.append(
            {
                "PartitionKey": entity["PartitionKey"],
                "RowKey": entity["RowKey"],
                "scenario": entity["scenario"],
                "create_datetime": entity["create_datetime"],
                "run_stage": entity.get("run_stage"),  # None if empty
            }
        )

    return scenarios


def list_scenarios(scenarios: list[dict]) -> list[str]:
    """
    Format scenarios for display in an interactive selection list.

    Args:
        scenarios: List of scenario dictionaries returned by fetch_scenarios().

    Returns:
        A list of formatted scenario labels for TUI selection, in the format
        "<scenario> (<create_datetime>) [<run_stage>]".
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


def update_entity(
    table_client: TableClient,
    scheme_choice: str,
    scenario_choice: str,
    tag_choice: str,
) -> None:
    """
    Update the run_stage tag for an existing scenario entity.

    Args:
        table_client: An authenticated TableClient.
        scheme_choice: Selected scheme code (PartitionKey).
        scenario_choice: User-selected scenario label.
        tag_choice: User-selected run-stage tag.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    scenario_choice_split = scenario_choice.split()
    scenario = scenario_choice_split[0]
    created = scenario_choice_split[1].strip("()")

    # RowKey is an entity-unique identifier, composed of name and datetime
    row_key = f"{scenario}-{created}"

    entity = table_client.get_entity(
        partition_key=scheme_choice,
        row_key=row_key,
    )

    entity["run_stage"] = tag_choice

    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.MERGE,  # update existing entity
    )
