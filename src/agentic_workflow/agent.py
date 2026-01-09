import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from agent_utils.agent_prompts import (
    CHART_SYSTEM_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
)

load_dotenv()

###
# TODO: Add prompts for each agent and tools
###

supervisor_provider = GoogleProvider(api_key=os.getenv("SUPERVISOR_KEY"))
supervisor_model = GoogleModel("gemini-2.5-pro", provider=supervisor_provider)
supervisor_agent = Agent(supervisor_model)

summarizer_provider = GoogleProvider(api_key=os.getenv("SUMMARIZER_KEY"))
summarizer_model = GoogleModel("gemini-2.5-flash-lite", provider=summarizer_provider)
summarizer_agent = Agent(summarizer_model)

chart_provider = GoogleProvider(api_key=os.getenv("CHART_KEY"))
chart_model = GoogleModel("gemini-2.5-flash-lite", provider=chart_provider)
chart_agent = Agent(chart_model)
