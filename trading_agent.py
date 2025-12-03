from openai import OpenAI
from dotenv import load_dotenv
import os
import json 

load_dotenv()
# read api key and optional base URL (for custom OpenAI-compatible endpoints)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Optional: set a custom API base (e.g. https://api.perplexity.ai). If not set, uses OpenAI default.
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

if OPENAI_API_BASE:
    # The OpenAI client accepts `api_base` to override the base URL.
    # Note: many third-party providers (including Perplexity) may NOT be fully
    # compatible with the OpenAI Responses API and model names used here.
    # You may need to adapt request parameters or switch to the provider's SDK.
    client = OpenAI(api_key=OPENAI_API_KEY, api_base=OPENAI_API_BASE)
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

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