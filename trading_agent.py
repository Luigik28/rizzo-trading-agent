from openai import OpenAI
from dotenv import load_dotenv
import os
import json 

load_dotenv()

# Configuration for OpenAI or compatible endpoints (e.g., Perplexity)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')  # e.g., https://api.perplexity.ai
USE_PERPLEXITY = 'perplexity' in (OPENAI_API_BASE or '').lower()

# Initialize client with base_url if provided
if OPENAI_API_BASE:
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
else:
    client = OpenAI(api_key=OPENAI_API_KEY)


def previsione_trading_agent(prompt):
    """
    Calls an LLM to generate a trading decision.
    Supports both OpenAI (gpt-5.1 Responses API) and Perplexity (Chat Completions API).
    """
    
    # JSON schema for the response
    # Note: direction is optional (only required for "open" and "close", not for "hold")
    trade_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "Type of trading operation to perform",
                "enum": ["open", "close", "hold"]
            },
            "symbol": {
                "type": "string",
                "description": "The cryptocurrency symbol to act on",
                "enum": ["BTC", "ETH", "SOL"]
            },
            "direction": {
                "type": ["string", "null"],
                "description": "Trade direction: long or short. Required for open/close, omit/null for hold.",
                "enum": ["long", "short", None]
            },
            "target_portion_of_balance": {
                "type": "number",
                "description": "Fraction 0.0-1.0",
                "minimum": 0,
                "maximum": 1
            },
            "leverage": {
                "type": "number",
                "description": "Leverage 1-10 (only for open)",
                "minimum": 1,
                "maximum": 10
            },
            "reason": {
                "type": "string",
                "description": "Brief explanation",
                "minLength": 1,
                "maxLength": 300
            }
        },
        "required": ["operation", "symbol", "target_portion_of_balance", "leverage", "reason"],
        "additionalProperties": False
    }
    
    def _sanitize_response(result: dict) -> dict:
        """
        Sanitize LLM response to ensure all required fields are present and valid.
        If direction is missing, set it based on operation:
        - "hold" -> None (direction not required for hold)
        - "open", "close" -> default to "long" (required for these operations)
        """
        # Ensure direction exists
        if "direction" not in result:
            if result.get("operation") == "hold":
                result["direction"] = None
            else:
                # For "open" and "close", direction is required; default to "long" if missing
                result["direction"] = "long"
        elif result.get("direction") is None and result.get("operation") != "hold":
            # If direction is explicitly null but operation is open/close, default to "long"
            result["direction"] = "long"
        
        # Ensure operation is valid
        if result.get("operation") not in ["open", "close", "hold"]:
            raise ValueError(f"Invalid operation: {result.get('operation')}")
        
        # Ensure symbol is valid
        if result.get("symbol") not in ["BTC", "ETH", "SOL"]:
            raise ValueError(f"Invalid symbol: {result.get('symbol')}")
        
        return result
    
    if USE_PERPLEXITY:
        # Perplexity uses Chat Completions API (compatible with OpenAI client)
        response = client.chat.completions.create(
            model="sonar",  # Perplexity model (or "sonar-pro" if available)
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a trading agent. Respond ONLY with valid JSON matching the provided schema. "
                        "No markdown, no extra text. "
                        "IMPORTANT: Always include all fields. "
                        "If operation is 'hold', set direction to null. "
                        "For 'open' and 'close', direction MUST be 'long' or 'short'."
                    )
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nRespond with JSON schema: {json.dumps(trade_schema)}"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        # Extract and parse response
        response_text = response.choices[0].message.content
        if response_text is None:
            raise ValueError("Perplexity returned empty response content")
        response_text = response_text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        result = json.loads(response_text.strip())
        return _sanitize_response(result)
    else:
        # Use OpenAI's Responses API (if available) or fallback to Chat Completions
        try:
            response = client.responses.create(
                model="gpt-5.1",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "trade_operation",
                        "strict": True,
                        "schema": trade_schema
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
                ]
            )
            result = json.loads(response.output_text)
            return _sanitize_response(result)
        except (AttributeError, TypeError):
            # Fallback to Chat Completions if Responses API not available
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a trading agent. Respond ONLY with valid JSON. No markdown, no extra text. "
                            "IMPORTANT: Always include all fields. "
                            "If operation is 'hold', set direction to null. "
                            "For 'open' and 'close', direction MUST be 'long' or 'short'."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nRespond with JSON schema: {json.dumps(trade_schema)}"
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            response_text = response.choices[0].message.content
            if response_text is None:
                raise ValueError("OpenAI fallback returned empty response content")
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            result = json.loads(response_text.strip())
            return _sanitize_response(result)