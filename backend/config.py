"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers (FREE MODELS)
COUNCIL_MODELS = [
    "google/gemini-2.0-flash-exp:free",           # Google Gemini 2.0 Flash - Very Fast
    "meta-llama/llama-3.3-70b-instruct:free",     # Meta Llama 3.3 70B - Dialogue
    "google/gemma-3-27b-it:free",                 # Google Gemma 3 27B - Vision+Text
    "tngtech/deepseek-r1t2-chimera:free",         # DeepSeek R1T2 Chimera 671B - Reasoning
]

# Chairman model - synthesizes final response (FREE)
CHAIRMAN_MODEL = "google/gemini-2.0-flash-exp:free"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
