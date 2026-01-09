import os

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from schema.agent_schema import (
    NvdSearchResponse,
)

load_dotenv()


summarizer_provider = GoogleProvider(api_key=os.getenv("SUMMARIZER_KEY"))
summarizer_model = GoogleModel("gemini-2.5-flash-lite", provider=summarizer_provider)
summarizer_agent = Agent(summarizer_model)


@summarizer_agent.tool
def cve_tool(ctx: RunContext[None], product_name: str) -> NvdSearchResponse:
    """
    Based on which vulnerability name was given pass the name as query for this tool,
    it will query the National Vulnerability Database api with a keywordSearch parameter

    ARGS:
        ctx[RunContext]: Context of the agent run
        product_name[str]: name of the product to get vulnerabilities
    """
    try:
        params = {"keywordSearch": product_name, "resultsPerPage": 1}
        with httpx.Client() as client:
            response = client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0", params=params
            )
        data = response.json()
        items = data.get("vulnerabilities", [])
    except Exception as e:
        raise e

    return NvdSearchResponse(
        id=items["id"], description=items["descriptions"][0]["value"]
    )
