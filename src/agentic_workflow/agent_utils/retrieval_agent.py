from typing import List

import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel

from .agent_prompts import RETRIEVAL_SYSTEM_PROMPT
from .schema.retrieval_schema import RetrievalResponse
from .tool_utils.handler import PsqlHandler
from .tool_utils.statistics import extract_data

retrieval_model = GoogleModel("gemini-2.5-flash-lite")
retrieval_agent = Agent(
    retrieval_model,
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
    output_type=RetrievalResponse,
)


def cve_issue(cve: str) -> bool:
    try:
        prefix, year, sequence_id = cve.split("-", maxsplit=2)
    except ValueError:
        return True

    if "CVE" not in prefix:
        return True
    if len(year) < 4 or not year.isdigit():
        return True

    return False


@retrieval_agent.tool
def device_vulnerability_tool(
    ctx: RunContext[None],
    device_list: List[str],
) -> RetrievalResponse:
    """
    This tool allows you to query the vulnerabilities table that holds information about the National Vulnerabilities Database (NVD)
    from a specific list with the name from devices, the list may contain 1 or more items but never 0.

    NOTE:
        If user didn't pass at least one item, don't run this tool

    ARGS:
        ctx[RunContext]: Context of the agent run
        device_list[List[str]]: A list that contains the name of the desired devices

    RETURNS:
        RetrievalResponse: A response containing the vulnerabilities of the devices
        the schema follows the following schema: List[str] = list of strings condensing the informations
        from devices
    """
    handler = PsqlHandler()
    try:
        data = handler.get_devices_vulnerabilities(device_list)
        summary = extract_data(data)
        return RetrievalResponse(list=summary)
    except Exception as e:
        raise ValueError("Wasn't able to retrieve data")


@retrieval_agent.tool
def api_search_tool(ctx: RunContext[None], cve_list: List[str]) -> RetrievalResponse:
    """
    Tool specialized in searching the nvd database api based at the cve code if only one cve is provided
    pass a list with only one cve, lesser than one shouldn't use this tool

    ARGS:
        ctx[RunContext]: Context of the agent run
        cves[List[str]]: List of CVE codes to search for

    CVE_STRUCTURE:
        cve follows an anatomy that must be obeyed:
            CVE-YYYY-NNNNN: Always start with CVE followed by '-' year '-' and number
    """
    broken_cve = [True if cve_issue(cve) else False for cve in cve_list]
    if True in broken_cve:
        raise ValueError("Invalid CVE format found")

    descriptions = []

    for cve in cve_list:
        with httpx.Client() as client:
            response = client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params={"cveId": cve},
            )
        data = response.json()
        if data.get("vulnerabilities", []):
            vulnerability = data["vulnerabilities"][0]["cve"]
            descriptions.append(
                f"cve:{cve}, status: {vulnerability['vulnStatus']}, description: {vulnerability['descriptions'][0]['value']}"
            )

    return RetrievalResponse(list=descriptions)


@retrieval_agent.tool
def list_devices_cve_tool(ctx: RunContext[None], row_limit: int) -> RetrievalResponse:
    """
    Tool specialized in getting all device_names from postgres db

    ARGS:
        ctx[RunContext]: Context of the agent run

    RETURNS:
        List[str]: List with the name of each device at the company database
    """
    if row_limit == 0:
        raise ValueError("You must select the maximun of devices to be shown")
    handler = PsqlHandler()
    devices_info = handler.list_devices_e_cves(row_limit)
    devices_info = [
        f"Device_name:{row['device_name']} - CVEs:{row['cves']} - vulnerability_title:{row['vulnerabilities']}"
        for row in devices_info
    ]
    return RetrievalResponse(list=devices_info)
