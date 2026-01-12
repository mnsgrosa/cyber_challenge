import logging
from typing import List, Optional, Tuple

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel

from .agent_prompts import BASIC_CRUD_SYSTEM_PROMPT
from .schema.context_schema import ToolResponse
from .tool_utils.handler import PsqlHandler

basic_crud_model = GoogleModel("gemini-2.5-flash-lite")
basic_crud_agent = Agent(
    basic_crud_model,
    deps_type=ToolResponse | None,
    system_prompt=BASIC_CRUD_SYSTEM_PROMPT,
    output_type=[bool, List[str]],
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@basic_crud_agent.tool
def insert_vulnerabilities_tool(
    ctx: RunContext[ToolResponse | None],
    vulnerabilities: List[Tuple[str, str, str, Optional[str]]],
) -> bool:
    """
    This tool inserts new data at vulnerabilities table you should give a list of tuples where you will input
    (title_of_vulnerability, vulnerability_description, vulnerability_discovery_date, vulnerability_cve) the only piece of information
    that the user has the option not to provide is vulnerability_cve, if the user does not provide the code place None, but
    any other information must be present, if the user gives only one set of possible input (title, descriptio, discovery_date, Optional[cve])
    input as a list with only one item

    ARGS:
        ctx: RunContext[ToolResponse]
        vulnerabilities: List[Tuple[str, str, str, str]]: this one must given with the following order:
            (title, descriptions, discovery_date, cve) if cve is not given (title, descriptions, discovery_date, None)
            the input must always be a list of tuples whether only one row was given: A row is configured by the previous
            given information
    RETURN:
        bool: If True the insertion was performed else an error ocurred
    """
    handler = PsqlHandler()
    inserted = handler.insert_vulnerabilities(vulnerabilities)
    return inserted


@basic_crud_agent.tool
def insert_asset_types_tool(
    ctx: RunContext[ToolResponse | None], assets_type_name: List[str]
) -> bool:
    """
    This tool inserts new assets_type_names to the asset_types table, the input must be a list with the name of the new asset type
    if the user gives only one entry you must input as a list with only one item

    ARGS:
        ctx: RunContext[ToolResponse]
        asset_names: List[str]: List containing a list of asset_names to be placed at asset_names table even if one item was given
        it will be generated a list with only one item

    RETURN:
        bool: Whether the operation was succesfull or not
    """
    handler = PsqlHandler()
    inserted = handler.insert_asset_types(assets_type_name)
    return inserted


@basic_crud_agent.tool
def insert_assets_tool(
    ctx: RunContext[ToolResponse | None], assets_e_types: List[Tuple[str, str]]
) -> List[str]:
    """
    This tool inserts a new asset_name associated with an asset_type_name that the user must choose, if the user doesn't provide
    one of the informations this tool musn't be called. If the user provides only one pair of informations pass as a list with only one tuple

    ARGS:
        ctx: RunContext[ToolResponse]
        assets_e_types: List[Tuple[str, str]]: Pair with name of the asset and the name which category this asset belongs to always should be
        given as a list of tuples and never should be given only one item always a pair of items -> asset_name and asset_type_name

    RETURN:
        List[str]: list of names requested that failed to be inserted, if the return is None than it means it was succesfull
    """
    handler = PsqlHandler()
    failed = handler.insert_assets(assets_e_types)
    return failed


@basic_crud_agent.tool
def insert_device_tool(
    ctx: RunContext[ToolResponse | None],
    device_asset_category: List[Tuple[str, str, str]],
) -> List[str]:
    """
    This tool inserts information at devices table, to insert any new infroamtion here the user must provide the device name,
    name of the asset and name of category, if one of this information is missing ignore this entry. the user must always tell
    this 3 informations

    ARGS:
        ctx: RunContext[ToolResponse]
        device_asset_category: List[Tuple[str, str, str]]: List containing a tuple with device_name, asset_name and category_name.
        this tool must be provided only informations that have available this 3 informations for insertion

    RETURN:
        List[str]: list of names requested that failed to be inserted, if the return is None than it means it was succesfull
    """
    handler = PsqlHandler()
    failed = handler.insert_device(device_asset_category)
    return failed


@basic_crud_agent.tool
def insert_device_category_tool(
    ctx: RunContext[ToolResponse | None], category_names: List[str]
) -> bool:
    """
    This tool inserts new device categories to the device_categories table, the input must be a list with the name of the new device category
    if the user gives only one entry you must input as a list with only one item

    ARGS:
        ctx: RunContext[ToolResponse]
        category_names: List[str]: List containing strings with new category_names for device_categories

    RETURN:
       bool: whether it was sucessfull or not
    """
    handler = PsqlHandler()
    inserted = handler.insert_device_category(category_names)
    return inserted


@basic_crud_agent.tool
def update_asset_tool(
    ctx: RunContext[ToolResponse | None], asset_names: List[Tuple[str, str]]
) -> List[str]:
    """
    This tool updates the assets table by giving a list of tuples with the first position being the old_asset_name and the second the new_asset_name
    both parameters must be explicited by the user

    ARGS:
        ctx: RunContext[ToolResponse]
        asset_names: List[Tuple[str, str]]: List containing strings with old asset names and new asset name

    RETURN:
        list[str]: List with failed insertion entries
    """
    handler = PsqlHandler()
    failed = handler.update_asset(asset_names)
    return failed


@basic_crud_agent.tool
def update_devices_info_tool(
    ctx: RunContext[ToolResponse | None],
    column: str,
    new_devices_info: List[Tuple[str, str]],
) -> List[str]:
    """
    This tool will update the devices table but it can update one of 3 columns available in this table
    devices_name, asset_name and category_name. The column must receive the values exactly as proposed
    the list with tuples must cointain the outdate_info followed by the new_info provided by the user
    no parameters must be missing
    ARGS:
        ctx: RunContext[ToolResponse]
        column: Column[str]: column that will be updated options are: [devices_names, asset_name, category_name]
        new: List[Tuple[str, str]]: Depending of each table the intem will vary, but they all follow the same logic (outdate_item, new_item)
        in this case it is possible to update the link between asset to devices table, category to devices and the name located in devcies

    RETURN:
        list[str]: List with failed insertion entries
    """
    handler = PsqlHandler()
    not_inserted = handler.update_devices_info(column, new_devices_info)
    return not_inserted


@basic_crud_agent.tool
def update_device_category_name_tool(
    ctx: RunContext[ToolResponse | None], change_list: List[Tuple[str, str]]
) -> List[str]:
    """
    This tool operates with the devices_categories table and it updates the information provided by the user
    the list with tuples must cointain the old_name followed by the new_name provided by the user
    no parameters must be missing
    ARGS:
        ctx: RunContext[ToolResponse]
        change_list: List[Tuple[str, str]]: Holds a list old_name followed by the new name for the device category
    RETURN:
        list[str]: List with failed insertion entries
    """
    handler = PsqlHandler()
    not_inserted = handler.update_device_category_name(change_list)
    return not_inserted
