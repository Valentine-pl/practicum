# config.py
"""
Configuration file for RAG Agent
All parameters and prompts are defined here
"""

# ==============================================================================
# MODEL CONFIGURATION
# ==============================================================================

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
TEMPERATURE = 0.7
MAX_TOKENS = 4096

# Available models:
# - us.anthropic.claude-sonnet-4-5-20250929-v1:0 (advanced)
# - us.anthropic.claude-haiku-4-5-20251001-v1:0 (fast & cheap)


# ==============================================================================
# AGENT CONFIGURATION
# ==============================================================================

MAX_ITERATIONS = 3  # Maximum tool use iterations before stopping


# ==============================================================================
# RETRIEVAL CONFIGURATION
# ==============================================================================

# Default retrieval settings
DEFAULT_K = 10
DEFAULT_SEARCH_TYPE = "HYBRID"  # Options: HYBRID, SEMANTIC, KEYWORD
DEFAULT_COMPANY_FILTER = None   # Set to company name to filter, or None for all

# Retrieval limits
MIN_K = 1
MAX_K = 50


# ==============================================================================
# CALCULATOR CONFIGURATION
# ==============================================================================

DEFAULT_PRECISION = 10  # Decimal places for calculations
DEFAULT_CALC_MODE = "evaluate"  # Options: evaluate, solve


# ==============================================================================
# SYSTEM PROMPT
# ==============================================================================

SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

**Available Tools:**

1. **calculator**: For precise mathematical calculations
   - Use for: arithmetic, trigonometry, logarithms, equations
   - Always use this instead of calculating yourself
   - Examples: "2^10", "sin(pi/4)", "log(100)"

2. **retrieve_documents**: For finding information from the knowledge base
   - Use for: searching documents, finding specific data
   - Supports filtering by company name
   - Returns ranked relevant chunks

**Guidelines:**
- Always use tools when you need calculations or document information
- Do not guess or calculate manually - use the calculator tool
- Cite sources when providing information from documents
- Be clear and concise in your responses
- If a tool fails, explain what happened and suggest alternatives
"""


# ==============================================================================
# OUTPUT CONFIGURATION
# ==============================================================================

SHOW_USAGE_STATS = True  # Show token usage and cost after each request
SHOW_TOOL_EXECUTION = True  # Show tool execution details
VERBOSE_MODE = False  # Extra debug information