"""
Combined Agent with DuckDuckGo Search and Julia Browser Tools
"""

import os
import sys
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Suppress all warnings including Anthropic cleanup warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# Completely disable all logging output
logging.disable(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL, handlers=[])

# Set all known loggers to CRITICAL and disable propagation
for logger_name in ["agno", "ddgs", "httpx", "anthropic", "openai", "google", "sqlalchemy", "rich"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.disabled = True

# Suppress stderr for specific exceptions
class SuppressedStderr:
    """Context manager to suppress specific stderr output"""
    def __init__(self):
        self.original_stderr = sys.stderr
        self.devnull = open(os.devnull, 'w')
        
    def write(self, message):
        # Filter out specific unwanted messages
        if any(phrase in str(message) for phrase in [
            "Exception ignored",
            "SyncHttpxClientWrapper",
            "__del__",
            "AttributeError: 'SyncHttpxClientWrapper'",
        ]):
            return
        self.original_stderr.write(message)
    
    def flush(self):
        self.original_stderr.flush()

# Replace stderr with filtered version
sys.stderr = SuppressedStderr()

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools
from .julia_browser_tools import get_julia_browser_tools

load_dotenv()


def get_db_path() -> str:
    """
    Get the cross-platform database path in user's home directory.
    Works on Windows, Linux, and macOS.
    
    Returns:
        str: Full path to the database file
    """
    home_dir = Path.home()
    openatlas_dir = home_dir / ".openatlas"
    openatlas_dir.mkdir(exist_ok=True)
    return str(openatlas_dir / "memory.db")


class CombinedAgent:
    """
    OpenAtlas Agent: An AI agent that combines web search (DuckDuckGo) and web browsing (julia_browser) capabilities.
    """
    
    def __init__(self, markdown: bool = True, model_id: str = "claude-sonnet-4-5", thinking: bool = False, enable_memory: bool = True):
        """
        Initialize the combined agent with DuckDuckGo and Julia Browser tools.
        Includes optional user memory management.
        
        Args:
            markdown (bool): Whether to use markdown formatting in responses
            model_id (str): LLM model ID (e.g., "claude-sonnet-4-5", "gpt-5", "gemini-2.0-flash")
            thinking (bool): Whether to enable reasoning tools for step-by-step thinking
            enable_memory (bool): Whether to enable automatic user memory management
        """
        # Setup database if memory is enabled
        db = None
        if enable_memory:
            db_path = get_db_path()
            db = SqliteDb(db_file=db_path)
        
        duckduckgo_tools = DuckDuckGoTools()
        julia_tools = get_julia_browser_tools()
        
        # Build tools list
        all_tools = [duckduckgo_tools] + julia_tools
        
        # Add reasoning tools if thinking is enabled
        if thinking:
            all_tools.append(ReasoningTools(add_instructions=True))  # type: ignore
        
        if "claude" in model_id.lower():
            model = Claude(id=model_id)
        elif "gpt" in model_id.lower() or "o1" in model_id.lower() or "o3" in model_id.lower():
            model = OpenAIChat(id=model_id)
        elif "gemini" in model_id.lower():
            model = Gemini(id=model_id)
        else:
            from agno.models.litellm import LiteLLM
            model = LiteLLM(id=model_id, name="LiteLLM")
        
        # Build description based on enabled features
        description_parts = ["OpenAtlas Agent: An AI browser that can search the web using DuckDuckGo and browse websites interactively."]
        if enable_memory:
            description_parts.append("I have automatic memory management to remember our conversations.")
        
        self.agent = Agent(
            model=model,
            tools=all_tools,
            markdown=markdown,
            db=db,
            enable_user_memories=enable_memory,
            description=" ".join(description_parts)
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
