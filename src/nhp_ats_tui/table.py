"""
Access and handle entities from Azure Table Storage.
"""

from azure.data.tables import TableClient, UpdateMode
from azure.identity import DefaultAzureCredential


def create_table_client(storage_account_name: str, table_name: str) -> TableClient:
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


def fetch_entities(table_client: TableClient, query: str = "") -> list[dict]:
    """
    Fetch all entities from the Azure TableClient.

    Create this object and filter it instead of making repeated Azure calls.

    Args:
        table (TableClient): An authenticated TableClient.
        query (str): A server-side OData query to filter the entities.

    Returns:
        A list of dicts that contain entity properties.
    """
    entities_iterator = table_client.query_entities(query_filter=query)
    entities = [dict(entity) for entity in entities_iterator]
    return entities


def list_unique_schemes(entities: list[dict]) -> list[str]:
    """
    Get a list of the unique dataset codes available from the entities.

    This will be shown to users as a selectable option in the TUI.

    Args:
        entities (list[dict]): Entities fetched from the Azure TableClient.
        dataset (str): The dataset code (e.g. R0A).

    Returns:
        A list of unique dataset code strings.
    """
    schemes = [entity["PartitionKey"] for entity in entities]
    unique_schemes = sorted(list(set(schemes)))  # case-sensitive, caps first
    return unique_schemes


def filter_entities_by_dataset(entities: list[dict], dataset: str) -> list[dict]:
    """
    Get the entities for a given dataset.

    Filter down the list of entities to the dataset of interest to the TUI user.

    Args:
        entities (list[dict]): Entities fetched from the Azure TableClient.
        dataset (str): The dataset code (e.g. R0A).

    Returns:
        A list of dicts (limited to a given dataset) that contain entity properties.
    """
    dataset_entities = [
        entity for entity in entities if entity["PartitionKey"] in dataset
    ]
    dataset_entities_sorted = sorted(
        dataset_entities,
        key=lambda x: x["create_datetime"],
        reverse=True,  # newest first
    )
    return dataset_entities_sorted


def create_scenario_label_lookup(entities: list[dict]) -> dict:
    """
    Generate a lookup of scenario labels to unique entity RowKeys.

    The scenario labels will be presented to the user in the TUI so they can
    select the entity they want to interact with. The corresponding entity's
    unique RowKey can be looked up given the scenario label.

    Args:
        entities (list[dict]): Entities fetched from the Azure TableClient.

    Returns:
        A dict with scenario labels as keys and entity RowKeys as values.
    """
    label_lookup = {}

    for entity in entities:
        scenario = entity["scenario"]
        create_datetime = entity["create_datetime"]
        if entity.get("run_stage") is None:
            run_stage = ""
        else:
            run_stage = f" [{entity['run_stage']}]"
        scenario_label = f"{scenario} ({create_datetime}){run_stage}"
        label_lookup.update({scenario_label: entity["RowKey"]})

    return label_lookup


def find_entity_by_label(
    entities: list[dict], scenario_label_choice: str, scenario_label_lookup: dict
) -> dict:
    """
    Get a specific entity given a user's scenario choice.

    Take the user's selected scenario label, look up the corresponding unique
    RowKey and filter the entities list to isolate the entity representing that
    scenario.

    Args:
        entities (list[dict]): Entities fetched from the Azure TableClient.
        scenario_label_choice (str): The scenario label chosen by the user.
        scenario_label_lookup (dict): The scenario-label-to-unique-RowKey lookup.

    Returns:
        A single entity as a dict.
    """
    row_key = scenario_label_lookup[scenario_label_choice]
    entity = [entity for entity in entities if entity["RowKey"] in row_key]
    entity_dict = entity[0]  # only one dict because RowKey is unique
    return entity_dict


def find_entity_sites(entity: dict, task_choice: str) -> tuple:
    """
    Get an entity's sites for a given activity type.

    Find the existing sites, if any, for the user's selected entity. This
    information will be presented back to the user in the TUI so they can
    see the current sites before they can choose to update them.

    Args:
        entity (dict): The entity from which to fetch a site property.
        task_choice (str): The task chosen by the user.

    Returns:
        A tuple with the activity type ("inpatients", "outpatients", "A&E") and
        existing sites (in the form "XYZ01,XYZ02", "ALL" or None).
    """
    if "inpatients" in task_choice:
        activity_type_choice = "inpatients"
        sites_existing = entity.get("sites_ip") or "none"
    elif "outpatients" in task_choice:
        activity_type_choice = "outpatients"
        sites_existing = entity.get("sites_op") or "none"
    elif "A&E" in task_choice:
        activity_type_choice = "A&E"
        sites_existing = entity.get("sites_aae") or "none"

    return activity_type_choice, sites_existing


def update_run_stage(
    table_client: TableClient,
    entity: dict,
    tag_choice: str | None,
) -> None:
    """
    Update the run-stage property for an existing scenario entity.

    Amend the ATS table by changing a single entity's run_stage value or by
    removing the property entirely, given the user's choice in the TUI.

    Args:
        table_client (TableClient): An authenticated TableClient.
        entity (dict): The single entity to be updated.
        tag_choice (str | None): Selected run-stage tag.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
    if tag_choice is None:
        entity.pop("run_stage", None)  # remove property entirely from entity
    else:
        entity["run_stage"] = tag_choice

    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.REPLACE,  # REPLACE not MERGE because run_stage may be removed
    )


def update_sites(
    table_client: TableClient,
    entity: dict,
    activity_type_choice: str,
    sites_provided: str | None,
) -> None:
    """
    Update a sites property for an existing scenario entity.

    Amend the ATS table by changing a single entity's sites_aae, sites_ip or
    sites_op value or by removing the property entirely, given the user's choice
    in the TUI.

    Args:
        table_client (TableClient): An authenticated TableClient.
        entity (dict): The single entity to be updated.
        activity_type_choice (str): Selected activity type.
        sites_provided (str | None): A comma-separated string of site codes.

    Returns:
        None. The entity is updated the corresponding Azure Table Storage.
    """
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
