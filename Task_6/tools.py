"""
tools.py - The two tools of the Student Assistant, plus their schemas.

IMPORTANT IDEA:
The SCHEMAS dictionary below is the ONE source of truth.
  1. agent.py sends it to the model (so the model knows how to call the tools)
  2. validator.py uses it to check the model's arguments
Because it is the same dictionary, the model and the validator can never disagree.
"""

import json
import math
from typing import Any, Callable, Dict, List

# ---------------------------------------------------------------------------
# Small hard-coded dataset (safe sample data, no real personal information)
# ---------------------------------------------------------------------------
STUDENT_MARKS: Dict[str, Dict[str, int]] = {
    "Logavarshini": {"Python": 85, "Java": 78, "AI": 92},
    "Arjun": {"Python": 66, "Java": 71, "AI": 58},
    "Meena": {"Python": 94, "Java": 88, "AI": 81},
}

# The only subjects the tools accept. Used in the enum of the schema.
ALLOWED_SUBJECTS: List[str] = ["Python", "Java", "AI"]


# ---------------------------------------------------------------------------
# Tool 1: get_marks
# ---------------------------------------------------------------------------
def get_marks(student_name: str, subject: str) -> str:
    """Return the marks of one student in one subject (as a JSON string)."""
    for known_name, subject_marks in STUDENT_MARKS.items():
        # Compare names ignoring upper/lower case and extra spaces.
        if known_name.lower() == student_name.strip().lower():
            if subject not in subject_marks:
                return f"ERROR: No marks stored for subject '{subject}'."
            return json.dumps(
                {"student_name": known_name, "subject": subject, "marks": subject_marks[subject]}
            )

    # The schema cannot know who exists in our dataset, so the tool itself checks.
    known = ", ".join(STUDENT_MARKS.keys())
    return f"ERROR: No student named '{student_name}'. Known students: {known}"


# ---------------------------------------------------------------------------
# Tool 2: calculate_grade
# ---------------------------------------------------------------------------
def calculate_grade(marks: float) -> str:
    """Convert marks (0-100) to a letter grade (as a JSON string)."""
    # Second line of defence: even if the validator is bypassed, never crash.
    if math.isnan(marks) or marks < 0 or marks > 100:
        return "ERROR: marks must be a number between 0 and 100."

    if marks >= 90:
        grade = "A"
    elif marks >= 80:
        grade = "B"
    elif marks >= 70:
        grade = "C"
    elif marks >= 60:
        grade = "D"
    else:
        grade = "F"

    return json.dumps({"marks": marks, "grade": grade})


# ---------------------------------------------------------------------------
# Tool name -> Python function. The agent uses this to find the function.
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS: Dict[str, Callable[..., str]] = {
    "get_marks": get_marks,
    "calculate_grade": calculate_grade,
}

# ---------------------------------------------------------------------------
# SCHEMAS - the single source of truth (JSON Schema format)
# ---------------------------------------------------------------------------
SCHEMAS: Dict[str, Dict[str, Any]] = {
    "get_marks": {
        "description": (
            "Look up the marks (0-100) of one student in one subject. "
            "Use this whenever the user asks for a student's mark."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_name": {
                    "type": "string",
                    "minLength": 1,
                    "description": "The student's first name, for example 'Logavarshini'.",
                },
                "subject": {
                    "type": "string",
                    "enum": ALLOWED_SUBJECTS,  # enum: only these three values are allowed
                    "description": "The subject to look up. Must be exactly one of the allowed values.",
                },
            },
            "required": ["student_name", "subject"],   # both arguments are mandatory
            "additionalProperties": False,             # no invented extra arguments
        },
    },
    "calculate_grade": {
        "description": (
            "Convert numeric marks into a letter grade. "
            "A = 90-100, B = 80-89, C = 70-79, D = 60-69, F = below 60."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "marks": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Marks between 0 and 100.",
                },
            },
            "required": ["marks"],
            "additionalProperties": False,
        },
    },
}


def get_tools_for_model(strict: bool = False) -> List[Dict[str, Any]]:
    """
    Convert SCHEMAS into the 'tools' list that the Chat Completions API expects.

    strict=True adds "strict": true to each function. Only some providers support it,
    so it is OFF by default (see STRICT_TOOLS in .env.example).
    """
    tools: List[Dict[str, Any]] = []
    for name, schema in SCHEMAS.items():
        function_definition: Dict[str, Any] = {
            "name": name,
            "description": schema["description"],
            "parameters": schema["parameters"],
        }
        if strict:
            function_definition["strict"] = True
        tools.append({"type": "function", "function": function_definition})
    return tools