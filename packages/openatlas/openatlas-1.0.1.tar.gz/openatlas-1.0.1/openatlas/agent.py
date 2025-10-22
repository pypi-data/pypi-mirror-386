"""
Combined Agent with DuckDuckGo Search and Julia Browser Tools
"""

import os
import logging
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from .julia_browser_tools import get_julia_browser_tools

load_dotenv()

logging.getLogger("agno").setLevel(logging.CRITICAL)
logging.getLogger("ddgs").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)


class CombinedAgent:
    """
    OpenAtlas Agent: An AI agent that combines web search (DuckDuckGo) and web browsing (julia_browser) capabilities.
    """
    
    def __init__(self, markdown: bool = True, model_id: str = "claude-sonnet-4-5"):
        """
        Initialize the combined agent with DuckDuckGo and Julia Browser tools.
        
        Args:
            markdown (bool): Whether to use markdown formatting in responses
            model_id (str): LLM model ID (e.g., "claude-sonnet-4-5", "gpt-5", "gemini-2.0-flash")
        """
        duckduckgo_tools = DuckDuckGoTools()
        julia_tools = get_julia_browser_tools()
        
        all_tools = [duckduckgo_tools] + julia_tools
        
        if "claude" in model_id.lower():
            model = Claude(id=model_id)
        elif "gpt" in model_id.lower() or "o1" in model_id.lower() or "o3" in model_id.lower():
            model = OpenAIChat(id=model_id)
        elif "gemini" in model_id.lower():
            model = Gemini(id=model_id)
        else:
            from agno.models.litellm import LiteLLM
            model = LiteLLM(id=model_id, name="LiteLLM")
        
        self.agent = Agent(
            model=model,
            tools=all_tools,
            markdown=markdown,
            description="OpenAtlas Agent: An AI browser that can search the web using DuckDuckGo and browse websites interactively."
        )
    
    def query(self, prompt: str, stream: bool = False):
        """
        Send a query to the agent.
        
        Args:
            prompt (str): The question or instruction for the agent
            stream (bool): Whether to stream the response
        """
        self.agent.print_response(prompt, stream=stream)
    
    def get_response(self, prompt: str) -> str:
        """
        Get a response from the agent as a string.
        
        Args:
            prompt (str): The question or instruction for the agent
        
        Returns:
            str: The agent's response
        """
        response = self.agent.run(prompt)
        return response.content if response.content else ""


if __name__ == "__main__":
    agent = CombinedAgent(markdown=True)
    
    print("\n=== Example 1: Web Search ===")
    agent.query("What's happening in France?", stream=True)
    
    print("\n\n=== Example 2: Browse Website ===")
    agent.query("Open the website https://news.ycombinator.com and tell me what you see", stream=True)
