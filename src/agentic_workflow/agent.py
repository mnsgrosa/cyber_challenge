import os

import httpx
import logfire
from agent_utils.agent_prompts import (
    CHART_SYSTEM_PROMPT,
    RETRIEVAL_SYSTEM_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
)
from agent_utils
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from agent_utils.retrieval_agent import retrieval_agent
load_dotenv()

###
# TODO: Add prompts for each agent and tools
###

supervisor_provider = GoogleProvider(api_key=os.getenv("SUPERVISOR_KEY"))
supervisor_model = GoogleModel("gemini-2.5-pro", provider=supervisor_provider)
supervisor_agent = Agent(supervisor_model)

@supervisor_agent.tool
def run_retrieval(ctx: RunContext[None], prompt:str):
    """
    Rewrite the prompt so the retrieval agent performs better

    ARGS:
        ctx[RunContext]: Agent context
        prompt: Rewritten prompt
    """
    pass
