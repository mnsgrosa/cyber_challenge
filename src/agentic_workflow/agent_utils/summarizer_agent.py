import os
from typing import Dict, List, Optional

import httpx
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from schema.summarizer_schema import (
    Vulnerability,
    VulnerabilityToolResponse,
)
from tool_utils.handler import PsqlHandler

load_dotenv()


summarizer_provider = GoogleProvider(api_key=os.getenv("SUMMARIZER_KEY"))
summarizer_model = GoogleModel("gemini-2.5-flash-lite", provider=summarizer_provider)
summarizer_agent = Agent(summarizer_model, output_type=VulnerabilityToolResponse)


@summarizer_agent.tool
def device_vulnerability_tool(
    ctx: RunContext[None],
    device_list: List[str],
) -> VulnerabilityToolResponse:
    """
    This tool allows you to query the vulnerabitlities table that holds informations about the National Vulnerabilities Database(NVD)
    here you will provide the CVE code from desired vulnerability

    NOTE:
        If user didn't pass at least on item dont run this tool

    ARGS:
        ctx[RunContext]: Context of the agent run
        device_list[List[str]]: A list that contains the name of the desired devices
    """
    handler = PsqlHandler()
    try:
        ans = handler.get_devices_vulnerabilities(device_list)
        ans = [Vulnerability(**row) for row in ans]
        return VulnerabilityToolResponse(vulnerabilities=ans)
    except Exception as e:
        raise ValueError("Wasnt able to retrieve data")
