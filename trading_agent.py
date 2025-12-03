from openai import OpenAI
import openai as _openai
from dotenv import load_dotenv
import os
import json 

load_dotenv()
# read api key and optional base URL (for custom OpenAI-compatible endpoints)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Optional: set a custom API base (e.g. https://api.perplexity.ai). If not set, uses OpenAI default.
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

# Some versions of the `openai` package expect configuration to be set on the module
# (e.g. `openai.api_key` / `openai.api_base`). Passing `api_base` to the `OpenAI`
# constructor may raise TypeError on some package versions, so we set module-level
# attributes when available and then instantiate the client without `api_base`.
if OPENAI_API_KEY:
    try:
        _openai.api_key = OPENAI_API_KEY
    except Exception:
        # fallback: set env var
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if OPENAI_API_BASE:
    # Try common attribute names across SDK versions
    if hasattr(_openai, "base_url"):
        _openai.base_url = OPENAI_API_BASE
    else:
        # Final fallback: set environment variable expected by some clients
        os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

# Instantiate client (no api_base kwarg to avoid TypeError on some versions)
client = OpenAI()

def previsione_trading_agent(prompt):
    response = client.responses.create(
    model="gpt-5.1",
    input=prompt,
    text={
        "format": {
        "type": "json_schema",
        "name": "trade_operation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
            "operation": {
                "type": "string",
                "description": "Type of trading operation to perform",
                "enum": [
                "open",
                "close",
                "hold"
                ]
            },
            "symbol": {
                "type": "string",
                "description": "The cryptocurrency symbol to act on",
                "enum": [
                "BTC",
                "ETH",
                "SOL"
                ]
            },
            "direction": {
                "type": "string",
                "description": "Trade direction: betting the price goes up (long) or down (short). For hold, may be omitted.",
                "enum": [
                "long",
                "short"
                ]
            },
            "target_portion_of_balance": {
                "type": "number",
                "description": "Fraction of (for open: balance, for close: position) to allocate/close; from 0.0 to 1.0 inclusive",
                "minimum": 0,
                "maximum": 1
            },
            "leverage": {
                "type": "number",
                "description": "Leverage multiplier (risk/reward, 1-10). Only applicable for 'open'.",
                "minimum": 1,
                "maximum": 10
            },
            "reason": {
                "type": "string",
                "description": "Brief explanation of the trading decision",
                "minLength": 1,
                "maxLength": 300
            }
            },
            "required": [
            "operation",
            "symbol",
            "direction",
            "target_portion_of_balance",
            "leverage",
            "reason"
            ],
            "additionalProperties": False
        }
        },
        "verbosity": "medium"
    },
    reasoning={
        "effort": "medium",
        "summary": "auto"
    },
    tools=[],
    store=True,
    include=[
        "reasoning.encrypted_content",
        "web_search_call.action.sources"
    ])
    return(json.loads(response.output_text))