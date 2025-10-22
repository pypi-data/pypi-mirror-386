#!/usr/bin/env python3
"""
OpenAtlas Agent CLI
An intelligent browser agent with web search and browsing capabilities
"""

import sys
import os
import logging
import argparse
from dotenv import load_dotenv
from .agent import CombinedAgent

load_dotenv()

logging.getLogger("agno").setLevel(logging.CRITICAL)
logging.getLogger("ddgs").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

VERSION = "v1.0.1"


def print_banner(model_id: str):
    """Print a welcome banner with configuration"""
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    display_dir = cwd.replace(home, "~") if cwd.startswith(home) else cwd
    
    banner = f"""
┌─────────────────────────────────────────────────────────────────┐
│ >_ OpenAtlas Agent ({VERSION})                                   │
└─────────────────────────────────────────────────────────────────┘

model:     {model_id:<20}  /model to change
directory: {display_dir}

To get started, describe a task or try one of these commands:

/model     - choose what model to use
/status    - show current session configuration  
/clear     - clear the screen
/help      - show detailed help information
/quit      - exit the CLI

Example tasks:
  • Search for the latest AI news
  • Open https://news.ycombinator.com and list the top stories
  • Find information about Python 3.13 features
"""
    print(banner)


def print_help():
    """Print detailed help information"""
    help_text = """
╔═══════════════════════════════════════════════════════════════╗
║  OpenAtlas Agent - Help & Commands                           ║
╚═══════════════════════════════════════════════════════════════╝

COMMANDS:
  /model     - Switch between AI models (Claude, GPT, Gemini)
  /status    - Display current model and configuration
  /clear     - Clear the terminal screen
  /help      - Show this help message
  /quit      - Exit the OpenAtlas Agent CLI

AVAILABLE MODELS:
  • claude-sonnet-4-5       - Anthropic Claude (Default)
  • gpt-4o                  - OpenAI GPT-4o
  • gemini-2.0-flash        - Google Gemini
  • Custom models via LiteLLM format

CAPABILITIES:
  Web Search (DuckDuckGo):
    - Search the web for current information
    - Get real-time news and updates
    - Find specific information quickly

  Web Browsing (Julia Browser):
    - Open and navigate websites
    - Click elements and fill forms
    - Scroll and interact with pages
    - Extract information from websites

EXAMPLE QUERIES:
  • What's happening in France today?
  • Search for the latest AI breakthroughs
  • Open github.com and search for Python projects
  • Browse to wikipedia.org and find information about Mars
  • What are the top stories on Hacker News?

API KEYS REQUIRED:
  ANTHROPIC_API_KEY  - For Claude models
  OPENAI_API_KEY     - For GPT models
  GEMINI_API_KEY     - For Gemini models
"""
    print(help_text)


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_model_input():
    """Get model ID from user"""
    print("\n🤖 Popular Models:")
    print("  1. claude-sonnet-4-5 (Anthropic) [Default]")
    print("  2. gpt-4o (OpenAI)")
    print("  3. gemini-2.0-flash (Google)")
    print("  4. Enter custom model ID (LiteLLM format)")

    choice = input("\n📋 Select (1-4) or press Enter for default: ").strip()

    if choice == "2":
        return "gpt-4o"
    elif choice == "3":
        return "gemini-2.0-flash"
    elif choice == "4":
        custom_model = input("Enter custom model ID: ").strip()
        return custom_model if custom_model else "claude-sonnet-4-5"
    else:
        return "claude-sonnet-4-5"


def print_status(model_id: str):
    """Print current session status"""
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    display_dir = cwd.replace(home, "~") if cwd.startswith(home) else cwd
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║  Session Configuration                                        ║
╚═══════════════════════════════════════════════════════════════╝

Version:   {VERSION}
Model:     {model_id}
Directory: {display_dir}

Available Tools:
  • DuckDuckGo Web Search
  • Julia Browser (13 tools)
    - Website navigation & interaction
    - Element clicking & form filling
    - Page scrolling & content extraction
""")


def main():
    """Main CLI loop"""
    parser = argparse.ArgumentParser(description='OpenAtlas Agent - AI Browser CLI')
    parser.add_argument('--model', type=str, help='LLM model ID to use')
    args = parser.parse_args()

    model_id = args.model or os.getenv('LLM_MODEL_ID', '').strip() or "claude-sonnet-4-5"

    try:
        agent = CombinedAgent(markdown=True, model_id=model_id)
        current_model = model_id
    except Exception as e:
        print(f"\n✗ Failed to initialize agent: {e}")
        print("\nMake sure you have the required API keys set:")
        print("  - ANTHROPIC_API_KEY for Claude models")
        print("  - OPENAI_API_KEY for OpenAI/GPT models")
        print("  - GEMINI_API_KEY for Gemini models")
        sys.exit(1)

    clear_screen()
    print_banner(current_model)

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            # Handle commands with / prefix
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command in ['/quit', '/exit', '/q']:
                    print("\nGoodbye! 👋")
                    break

                elif command in ['/help', '/h']:
                    print_help()
                    continue

                elif command in ['/clear', '/cls']:
                    clear_screen()
                    print_banner(current_model)
                    continue

                elif command in ['/status']:
                    print_status(current_model)
                    continue

                elif command in ['/model']:
                    new_model = get_model_input()
                    if new_model != current_model:
                        print(f"\nSwitching to {new_model}...")
                        try:
                            agent = CombinedAgent(markdown=True, model_id=new_model)
                            current_model = new_model
                            print(f"✓ Now using {new_model}")
                            clear_screen()
                            print_banner(current_model)
                        except Exception as e:
                            print(f"✗ Failed to switch model: {e}")
                    continue

                else:
                    print(f"Unknown command: {user_input}")
                    print("Type /help for available commands")
                    continue

            # Regular query to the agent
            print()
            agent.query(user_input, stream=True)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break

        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("Please try again or type /help for assistance.")


if __name__ == "__main__":
    main()
