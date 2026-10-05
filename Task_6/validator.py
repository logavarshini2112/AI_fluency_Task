"""
validator.py - Checks tool-call arguments BEFORE we run any tool.

Rule of this file: normal problems never raise exceptions.
They return a clear error string, so the agent can send it back to the model.
"""

import json
from typing import Any, Dict, Optional, Tuple

from tools import SCHEMAS

# Friendly names used in error messages.
TYPE_NAMES = {
    "string": "a string",
    "number": "a number",
    "integer": "an integer",
    "boolean": "a boolean",
}


def parse_json_arguments(raw_arguments: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Stage 1: turn the model's argument text into a Python dict.
    Returns (arguments, None) on success or (None, error_message) on failure.
    """
    # A tool call with no arguments may arrive as "" or None -> treat as {}.
    if raw_arguments is None or raw_arguments.strip() == "":
        return {}, None

    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError as err:
        return None, f"Arguments are not valid JSON ({err.msg} at position {err.pos})"

    if not isinstance(parsed, dict):
        return None, f"Arguments must be a JSON object, but got {type(parsed).__name__}"

    return parsed, None


def _matches_type(value: Any, expected_type: str) -> bool:
    """Check one value against a JSON Schema type name."""
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        # In Python, True/False are also ints. A boolean is NOT a valid number here.
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True  # a type we do not check


def validate_arguments(tool_name: str, arguments: Any) -> Optional[str]:
    """
    Stage 3: validate arguments against SCHEMAS.
    Returns None when valid, otherwise a clear error message.
    """
    if tool_name not in SCHEMAS:
        available = ", ".join(SCHEMAS.keys())
        return f"Unknown tool: {tool_name}. Available tools: {available}"

    if not isinstance(arguments, dict):
        return "Arguments must be a JSON object"

    schema = SCHEMAS[tool_name]["parameters"]
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    errors = []

    # 1. Missing required arguments
    for name in required:
        if name not in arguments:
            errors.append(f"Missing required argument: {name}")

    # 2. Invented (extra) arguments
    if schema.get("additionalProperties") is False:
        for name in arguments:
            if name not in properties:
                errors.append(f"Unexpected argument: {name}")

    # 3. Type, enum, range and length checks for the arguments that were given
    for name, value in arguments.items():
        rule = properties.get(name)
        if rule is None:
            continue  # already reported above if extras are not allowed

        expected_type = rule.get("type")
        if expected_type and not _matches_type(value, expected_type):
            readable = TYPE_NAMES.get(expected_type, expected_type)
            errors.append(f"Argument {name} must be {readable}")
            continue  # no point checking enum/range on a wrong type

        if "enum" in rule and value not in rule["enum"]:
            allowed = ", ".join(str(item) for item in rule["enum"])
            errors.append(f"Argument {name} must be one of: {allowed}")

        if isinstance(value, str) and "minLength" in rule and len(value.strip()) < rule["minLength"]:
            errors.append(f"Argument {name} must not be empty")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            low = rule.get("minimum")
            high = rule.get("maximum")
            too_low = low is not None and value < low
            too_high = high is not None and value > high
            if too_low or too_high:
                if low is not None and high is not None:
                    errors.append(f"Argument {name} must be between {low} and {high}")
                elif low is not None:
                    errors.append(f"Argument {name} must be at least {low}")
                else:
                    errors.append(f"Argument {name} must be at most {high}")

    if errors:
        return "; ".join(errors)
    return None


if __name__ == "__main__":
    # Quick self-test: run `python validator.py` and take the "validator output" screenshot.
    samples = [
        ("get_marks", {"student_name": "Logavarshini", "subject": "Python"}),   # valid
        ("get_marks", {"student_name": "Logavarshini"}),                        # missing
        ("get_marks", {"student_name": "Logavarshini", "subject": "Python", "age": 20}),  # extra
        ("get_marks", {"student_name": 123, "subject": "Python"}),              # wrong type
        ("get_marks", {"student_name": "Logavarshini", "subject": "Cricket"}),  # enum
        ("calculate_grade", {"marks": 150}),                                    # out of range
        ("get_attendance", {"student_name": "Logavarshini"}),                   # unknown tool
    ]
    for tool_name, args in samples:
        result = validate_arguments(tool_name, args)
        print(f"{tool_name} {args}\n   -> {'VALID' if result is None else result}\n")
    print("JSON parse test:", parse_json_arguments("{'subject': 'Python'}"))