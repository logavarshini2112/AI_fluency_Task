"""
fault_injection.py - Deliberately feed BROKEN tool calls to the handler.

This script does NOT call the LLM and needs no internet or API key.
It pretends to be a misbehaving model by writing the broken tool calls by hand,
then sends them through handle_tool_call() - the exact function agent.py uses.

Run:  python fault_injection.py
"""

from typing import Dict, List

from agent import MAX_IDENTICAL_CALLS, handle_tool_call, register_call

# Each fault: description, tool name, raw argument text (exactly what a model would send),
# and whether we EXPECT the handler to return an ERROR string.
FAULTS: List[Dict] = [
    {
        "description": "Invalid JSON (single quotes instead of double quotes)",
        "tool": "get_marks",
        "raw": "{'student_name': 'Logavarshini', 'subject': 'Python'}",
        "expect_error": True,
    },
    {
        "description": "Unknown tool (get_attendance does not exist)",
        "tool": "get_attendance",
        "raw": '{"student_name": "Logavarshini"}',
        "expect_error": True,
    },
    {
        "description": "Missing required argument (subject is missing)",
        "tool": "get_marks",
        "raw": '{"student_name": "Logavarshini"}',
        "expect_error": True,
    },
    {
        "description": "Wrong type (marks is a string, not a number)",
        "tool": "calculate_grade",
        "raw": '{"marks": "eighty-five"}',
        "expect_error": True,
    },
    {
        "description": "Enum violation (Cricket is not an allowed subject)",
        "tool": "get_marks",
        "raw": '{"student_name": "Logavarshini", "subject": "Cricket"}',
        "expect_error": True,
    },
    {
        "description": "Invented argument (age is not in the schema)",
        "tool": "get_marks",
        "raw": '{"student_name": "Logavarshini", "subject": "Python", "age": 20}',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 1: marks out of range (150 is above the maximum of 100)",
        "tool": "calculate_grade",
        "raw": '{"marks": 150}',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 2: empty student_name",
        "tool": "get_marks",
        "raw": '{"student_name": "", "subject": "Python"}',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 3: valid JSON but a list instead of an object",
        "tool": "get_marks",
        "raw": '["Logavarshini", "Python"]',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 4: boolean sent where a number is expected (Python treats True as 1)",
        "tool": "calculate_grade",
        "raw": '{"marks": true}',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 5: truncated JSON (like a reply cut off by finish_reason='length')",
        "tool": "get_marks",
        "raw": '{"student_name": "Logavarshini", "subje',
        "expect_error": True,
    },
    {
        "description": "CUSTOM 6: passes the schema but the student does not exist",
        "tool": "get_marks",
        "raw": '{"student_name": "Nobody", "subject": "Python"}',
        "expect_error": True,
    },
    {
        "description": "CONTROL: a perfectly valid call (must NOT be an error)",
        "tool": "get_marks",
        "raw": '{"student_name": "Logavarshini", "subject": "Python"}',
        "expect_error": False,
    },
]


def run_faults() -> None:
    continued_count = 0
    as_expected_count = 0

    for number, fault in enumerate(FAULTS, start=1):
        print("=" * 70)
        print(f"Fault {number}: {fault['description']}")
        print(f"  Input tool     : {fault['tool']}")
        print(f"  Input arguments: {fault['raw']}")

        try:
            returned = handle_tool_call(fault["tool"], fault["raw"])
            continued = True
        except Exception as err:  # In this TEST script we WANT to detect a crash and report it.
            returned = f"CRASH: {type(err).__name__}: {err}"
            continued = False

        is_error = returned.startswith("ERROR") or returned.startswith("CRASH")
        as_expected = is_error == fault["expect_error"]

        continued_count += int(continued)
        as_expected_count += int(as_expected)

        print(f"  Returned message: {returned}")
        print(f"  Handler continued (no crash)? {'YES' if continued else 'NO'}")
        print(f"  Behaved as expected?          {'YES' if as_expected else 'NO'}")

    print("=" * 70)
    print(f"Handler continued without crashing in {continued_count}/{len(FAULTS)} tests.")
    print(f"Behaved as expected in {as_expected_count}/{len(FAULTS)} tests.")


def run_repeated_call_simulation() -> None:
    """Offline check of the 'repeated identical calls' guard used by the agent loop."""
    print("\n" + "=" * 70)
    print("Repeated identical call simulation (same call sent again and again)")
    print(f"The agent stops when the same call is seen more than {MAX_IDENTICAL_CALLS} times.")
    seen_calls: Dict[str, int] = {}
    for attempt in range(1, MAX_IDENTICAL_CALLS + 3):
        times = register_call(seen_calls, "get_marks", '{"student_name": "Logavarshini", "subject": "Cricket"}')
        decision = "STOP the agent" if times > MAX_IDENTICAL_CALLS else "allow"
        print(f"  identical call #{attempt}: seen {times} time(s) -> {decision}")


if __name__ == "__main__":
    run_faults()
    run_repeated_call_simulation()