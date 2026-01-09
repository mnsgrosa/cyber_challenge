import os

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

load_dotenv()

chart_provider = GoogleProvider(api_key=os.getenv("CHART_KEY"))
chart_model = GoogleModel("gemini-2.5-flash-lite", provider=chart_provider)
chart_agent = Agent(chart_model)


@chart_agent.tool
def graph_points(
    ctx: RunContext[None], vulnerability: str, start_date: str, end_date: str
):
    """
    Based on chosen vulnerability return datapoints throughout the timeline
    """
    pass
