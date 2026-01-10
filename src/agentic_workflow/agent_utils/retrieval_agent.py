import os
from typing import List

import httpx
from agent_prompts import RETRIEVAL_SYSTEM_PROMPT
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from schema.retrieval_schema import (
    ListerToolResponse,
    NvdToolResponse,
    VulnerabilityToolResponse,
)
from tool_utils.handler import PsqlHandler
from tool_utils.statistics import extract_data

load_dotenv()


retrieval_provider = GoogleProvider(api_key=os.getenv("RETRIEVAL_KEY"))
retrieval_model = GoogleModel("gemini-2.5-flash-lite", provider=retrieval_provider)
retrieval_agent = Agent(
    retrieval_model,
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
    output_type=[ListerToolResponse, VulnerabilityToolResponse, NvdToolResponse],
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
    if len(sequence_id) < 5 or not sequence_id.isdigit():
        return True

    return False


@retrieval_agent.tool
def device_vulnerability_tool(
    ctx: RunContext[None],
    device_list: List[str],
) -> VulnerabilityToolResponse:
    """
    This tool allows you to query the vulnerabilities table that holds information about the National Vulnerabilities Database (NVD)
    from a specific list with the name from devices, the list may contain 1 or more items but never 0.

    NOTE:
        If user didn't pass at least one item, don't run this tool

    ARGS:
        ctx[RunContext]: Context of the agent run
        device_list[List[str]]: A list that contains the name of the desired devices

    RETURNS:
        VulnerabilityToolResponse: A response containing the vulnerabilities of the devices
        the schema follows the following schema
            name[str]: Name of the device
            category_name[str]: Category that the device belongs to
            description[str]: Vulnerabilities description
            cve[str]: CVE code from National Vulnerability Database
            discovery_date[date]: Date that the vulnerability got discovered
    """
    handler = PsqlHandler()
    try:
        data = handler.get_devices_vulnerabilities(device_list)
        summary = extract_data(data)
        return VulnerabilityToolResponse(vulnerabilities=summary)
    except Exception as e:
        raise ValueError("Wasn't able to retrieve data")


@retrieval_agent.tool
def cve_search_tool(ctx: RunContext[None], cve_list: List[str]) -> NvdToolResponse:
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

    return NvdToolResponse(descriptions=descriptions)


@retrieval_agent.tool
def cve_list_tool(ctx: RunContext[None]) -> ListerToolResponse:
    """
    Tool specialized in getting all device_names from postgres db

    ARGS:
        ctx[RunContext]: Context of the agent run

    RETURNS:
        List[str]: List with the name of each device at the company database
    """
    handler = PsqlHandler()
    device_names = handler.list_devices()
    return ListerToolResponse(list=device_names)
