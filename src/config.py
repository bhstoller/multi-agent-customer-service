"""
This module handles all if the configuration (environment variables and constants)
that are used throughout the notebooks and scripts.
"""

# Imports
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


# ======================================================================================
# API CONFIGURATION
# ======================================================================================
# This gets the Google API key from .env

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
"""Google API Key for Gemini models. Set via GOOGLE_API_KEY env var."""


# ======================================================================================
# SERVER CONFIGURATION
# ======================================================================================
# This gets the NGrok Authentication token, MPC server url, and agents ports from .env

# Ngrok configuration
NGROK_AUTHTOKEN = os.getenv('NGROK_AUTHTOKEN', '')

# Avoid NGrok if authtoken is not found
USE_NGROK = bool(NGROK_AUTHTOKEN)

# MCP Server
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL')

# Agent Servers
ROUTER_HOST = os.getenv('ROUTER_HOST', 'localhost')
ROUTER_PORT = int(os.getenv('ROUTER_PORT', 10019))
ROUTER_URL = f'http://{ROUTER_HOST}:{ROUTER_PORT}'

SUPPORT_HOST = os.getenv('SUPPORT_HOST', 'localhost')
SUPPORT_PORT = int(os.getenv('SUPPORT_PORT', 10021))
SUPPORT_URL = f'http://{SUPPORT_HOST}:{SUPPORT_PORT}'

CUSTOMER_DATA_HOST = os.getenv('CUSTOMER_DATA_HOST', 'localhost')
CUSTOMER_DATA_PORT = int(os.getenv('CUSTOMER_DATA_PORT', 10020))
CUSTOMER_DATA_URL = f'http://{CUSTOMER_DATA_HOST}:{CUSTOMER_DATA_PORT}'


# ======================================================================================
# DATABASE CONFIGURATION
# ======================================================================================
# This gets the path to the SQLite database file (support.db)
# support.db is created by running the database_setup.py script we were given.

REPO_ROOT = Path(__file__).parent.parent  # Go up from src/ to root
DB_PATH = os.getenv('DB_PATH', str(REPO_ROOT / 'support.db'))


# ======================================================================================
# MODEL CONFIGURATION
# ======================================================================================
# This defines the LLM model to be used for the agents

LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.0-flash')


# ======================================================================================
# AGENT CONFIGURATION
# ======================================================================================
# This defines the names of the agents used/created in agents.py

# Agent names (for A2A identification)
ROUTER_AGENT_NAME = 'router_agent'
SUPPORT_AGENT_NAME = 'support_agent'
CUSTOMER_DATA_AGENT_NAME = 'customer_data_agent'


# ======================================================================================
# LOGGING CONFIGURATION
# ======================================================================================
# This sets the logging level used

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# ======================================================================================
# DEBUGGING
# ======================================================================================
# This enables debug mode if true

DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')


# ======================================================================================
# Validation
# ======================================================================================
# This function confirms that the information read above was successfully retrieved

def validate_config():
    """
    Validate that required configuration is set, and raise ValueError if missing.
    """
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is required. "
            "Get one at: https://aistudio.google.com/app/apikey"
        )
    
    if not MCP_SERVER_URL:
        raise ValueError(
            "MCP_SERVER_URL environment variable is required. "
            "Set it in your .env file (e.g., your ngrok URL or localhost)"
        )


# Run validation on import
if __name__ == '__main__':
    # Print configuration for debugging
    print("Current Configuration:")
    print(f"  Google API Key: {'***' if GOOGLE_API_KEY else 'NOT SET'}")
    print(f"  MCP Server URL: {MCP_SERVER_URL}")
    print(f"  Ngrok Enabled: {USE_NGROK}")
    print(f"  Router URL: {ROUTER_URL}")
    print(f"  Support URL: {SUPPORT_URL}")
    print(f"  Customer Data URL: {CUSTOMER_DATA_URL}")
    print(f"  Database Path: {DB_PATH}")
    print(f"  LLM Model: {LLM_MODEL}")
    print(f"  Debug Mode: {DEBUG}")