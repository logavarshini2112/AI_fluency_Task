"""
structured_outputs.py - Ask the SAME extraction question three ways:
  1. Normal (no constraint)
  2. JSON mode
  3. Schema mode (JSON Schema, if the provider supports it)

If the provider does not support a mode, we catch the error and report it.
We never fake a result.

Run:  python structured_outputs.py
"""

import json
from typing import Any, Dict, Optional

from openai import APIError, OpenAI

from agent import MODEL, create_client

SENTENCE = "Logavarshini is a second-year student in Artificial Intelligence and Data Science."
QUESTION = (
    "Extract the student's name, department, and year from this sentence: "
    f"{SENTENCE}"
)

# The JSON Schema used in schema mode.
STUDENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "department": {"type": "string"},
        "year": {"type": "integer"},
    },
    "required": ["name", "department", "year"],
    "additionalProperties": False,
}


def try_parse_json(text: Optional[str]) -> str:
    """Return a readable description of whether the reply parsed as JSON."""
    if not text:
        return "(empty reply, nothing to parse)"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as err:
        return f"NOT valid JSON ({err.msg})"
    return f"parsed OK -> {parsed}"


def run_mode(client: OpenAI, mode_name: str, user_prompt: str, response_format: Optional[Dict[str, Any]]) -> None:
    print("=" * 70)
    print(f"MODE: {mode_name}")

    request: Dict[str, Any] = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": 800,
    }
    if response_format is not None:
        request["response_format"] = response_format

    try:
        response = client.chat.completions.create(**request)
    except APIError as err:
        print(f"  Raw model reply : (none)")
        print(f"  Parsed result   : (none)")
        print(f"  ERROR: the provider rejected or does not support this mode -> {err}")
        return

    reply = response.choices[0].message.content
    print(f"  Raw model reply : {reply}")
    print(f"  Parsed result   : {try_parse_json(reply)}")

    # Some providers accept the parameter but ignore it, so also check the keys ourselves.
    if response_format is not None and reply:
        try:
            parsed = json.loads(reply)
        except json.JSONDecodeError:
            return
        if isinstance(parsed, dict):
            missing = [key for key in STUDENT_SCHEMA["required"] if key not in parsed]
            extra = [key for key in parsed if key not in STUDENT_SCHEMA["properties"]]
            print(f"  Key check       : missing={missing or 'none'}, extra={extra or 'none'}")


def main() -> None:
    client = create_client()

    # 1. Normal, unconstrained
    run_mode(client, "1. Normal (no constraint)", QUESTION, None)

    # 2. JSON mode (many providers require the word "JSON" in the prompt)
    json_prompt = QUESTION + "\nReply with JSON only, using the keys: name, department, year."
    run_mode(client, "2. JSON mode", json_prompt, {"type": "json_object"})

    # 3. Schema mode (strict JSON Schema)
    schema_format = {
        "type": "json_schema",
        "json_schema": {"name": "student_info", "strict": True, "schema": STUDENT_SCHEMA},
    }
    run_mode(client, "3. Schema mode (json_schema)", QUESTION, schema_format)


if __name__ == "__main__":
    main()