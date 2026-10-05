"""
agent.py - A manual, beginner-friendly tool-calling agent loop.

Uses the OpenAI Python client with ANY OpenAI-compatible provider
(Groq, Ollama, vLLM, ...). Provider settings come from the .env file.

REMEMBER: the model never runs our Python functions.
It only asks for a call (as text). OUR code validates and runs the function.

Usage:
    python agent.py                 -> run all 4 test questions
    python agent.py 3               -> run test question number 3
    python agent.py "Your own question here"
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import APIError, OpenAI

from tools import TOOL_FUNCTIONS, get_tools_for_model
from validator import parse_json_arguments, validate_arguments

# ---------------------------------------------------------------------------
# Configuration (read from .env - NEVER write a key in the code)
# ---------------------------------------------------------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

MAX_STEPS = int(os.getenv("MAX_STEPS", "6"))               # max model calls per question
START_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))    # first max_tokens value
MAX_TOKENS_LIMIT = 4096                                    # never grow beyond this
MAX_LENGTH_RETRIES = 3                                     # retries when finish_reason == "length"
MAX_IDENTICAL_CALLS = 2                                    # the 3rd identical call stops the agent
USE_STRICT_TOOLS = os.getenv("STRICT_TOOLS", "false").lower() == "true"

SYSTEM_PROMPT = (
    "You are a helpful Student Assistant. "
    "Use the provided tools to look up student marks and to calculate grades. "
    "Never invent marks. "
    "If a tool returns an error, read the error message carefully, then either "
    "fix the tool call or explain the problem to the user. "
    "If the question does not need a tool, answer directly."
)

# The four test questions required by the task.
QUESTIONS: Dict[int, str] = {
    1: "What is Logavarshini's Python mark?",
    2: "What is Logavarshini's Python mark and what grade does that mark correspond to?",
    3: "Get Logavarshini's Cricket mark.",
    4: "Explain what a grade means.",
}


def log(message: str) -> None:
    """All printing goes through here so the output style stays consistent."""
    print(message)


def create_client() -> OpenAI:
    """Create the OpenAI client pointing at the provider from .env."""
    missing = [
        name for name, value in (("API_KEY", API_KEY), ("BASE_URL", BASE_URL), ("MODEL", MODEL))
        if not value
    ]
    if missing:
        raise SystemExit(
            f"Missing settings in .env: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your provider details.\n"
            "(Ollama ignores the key, but the client still needs some non-empty value in API_KEY.)"
        )
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ---------------------------------------------------------------------------
# The 4-stage handler. fault_injection.py imports and uses THIS function.
# It never raises for normal problems: every failure becomes a string.
# ---------------------------------------------------------------------------
def handle_tool_call(tool_name: str, raw_arguments: Optional[str]) -> str:
    """Parse -> look up -> validate -> execute. Returns the tool result as a string."""

    # Stage 1: parse the JSON arguments
    arguments, parse_error = parse_json_arguments(raw_arguments)
    if parse_error is not None:
        log(f"    Stage 1 (parse JSON)   FAILED: {parse_error}")
        return f"ERROR: {parse_error}. Please send the arguments as valid JSON."
    log("    Stage 1 (parse JSON)   OK")

    # Stage 2: look up the tool
    if tool_name not in TOOL_FUNCTIONS:
        available = ", ".join(TOOL_FUNCTIONS.keys())
        log(f"    Stage 2 (find tool)    FAILED: unknown tool '{tool_name}'")
        return f"ERROR: Unknown tool '{tool_name}'. Available tools: {available}"
    log("    Stage 2 (find tool)    OK")

    # Stage 3: validate the arguments against the schema
    validation_error = validate_arguments(tool_name, arguments)
    if validation_error is not None:
        log(f"    Stage 3 (validate)     FAILED: {validation_error}")
        return f"ERROR: Invalid arguments for {tool_name}: {validation_error}. Fix the call and try again."
    log("    Stage 3 (validate)     OK")

    # Stage 4: execute (only reached after validation succeeded)
    try:
        result = TOOL_FUNCTIONS[tool_name](**arguments)
    except Exception as err:  # explicit and reported, never silent
        log(f"    Stage 4 (execute)      CRASHED: {type(err).__name__}: {err}")
        return f"ERROR: The tool '{tool_name}' failed while running: {type(err).__name__}: {err}"

    result = str(result)
    log(f"    Stage 4 (execute)      OK -> {result}")
    return result


# ---------------------------------------------------------------------------
# Repeated identical call detection
# ---------------------------------------------------------------------------
def register_call(seen_calls: Dict[str, int], tool_name: str, raw_arguments: Optional[str]) -> int:
    """Remember a tool call and return how many times this exact call has been seen."""
    text = raw_arguments or ""
    try:
        # Normalise so {"a":1,"b":2} and {"b":2,"a":1} count as the same call.
        text = json.dumps(json.loads(text), sort_keys=True)
    except json.JSONDecodeError:
        pass  # invalid JSON: use the raw text as the signature

    signature = f"{tool_name}:{text}"
    seen_calls[signature] = seen_calls.get(signature, 0) + 1
    return seen_calls[signature]


# ---------------------------------------------------------------------------
# Calling the model (with retry when the answer was cut off)
# ---------------------------------------------------------------------------
def call_model(client: OpenAI, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], stats: Dict[str, Any]) -> Any:
    """Call Chat Completions. If finish_reason == 'length', retry with bigger max_tokens."""
    max_tokens = START_MAX_TOKENS
    choice = None

    for attempt in range(MAX_LENGTH_RETRIES + 1):
        log(f"  Calling model (model={MODEL}, max_tokens={max_tokens})")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",      # the model decides whether to use a tool
            max_tokens=max_tokens,
            # No stream=True: streaming is not used inside the agent loop.
        )
        choice = response.choices[0]

        if choice.finish_reason != "length":
            return choice

        # finish_reason == "length": the reply was cut off. Never run a cut-off tool call.
        new_max_tokens = min(max_tokens * 2, MAX_TOKENS_LIMIT)
        if attempt == MAX_LENGTH_RETRIES or new_max_tokens == max_tokens:
            return choice  # give up; run_agent will report it
        stats["length_retries"] += 1
        log(f"  RETRY: finish_reason was 'length' (truncated). Retrying with max_tokens={new_max_tokens}")
        max_tokens = new_max_tokens

    return choice


def print_summary(stats: Dict[str, Any], final_answer: str) -> None:
    """Print the numbers you need for the Agent Behaviour table in analysis.md."""
    log("\n  ===== RUN SUMMARY =====")
    log(f"  Steps (model calls)     : {stats['steps']}")
    log(f"  Tool calls              : {stats['tool_calls'] if stats['tool_calls'] else 'none'}")
    log(f"  Parallel calls?         : {'yes' if stats['parallel'] else 'no'}")
    log(f"  finish_reason=length?   : {'yes (' + str(stats['length_retries']) + ' retries)' if stats['length_retries'] else 'no'}")
    log(f"  Final answer            : {final_answer}")


# ---------------------------------------------------------------------------
# The agent loop
# ---------------------------------------------------------------------------
def run_agent(client: OpenAI, user_question: str) -> str:
    """Run the manual agent loop for one question and return the final answer."""
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]
    tools = get_tools_for_model(strict=USE_STRICT_TOOLS)
    seen_calls: Dict[str, int] = {}
    stats: Dict[str, Any] = {"steps": 0, "tool_calls": [], "parallel": False, "length_retries": 0}

    for step in range(1, MAX_STEPS + 1):
        stats["steps"] = step
        log(f"\n--- Step {step} of max {MAX_STEPS} ---")

        # 1. Send messages + tools to the model
        choice = call_model(client, messages, tools, stats)
        message = choice.message
        finish_reason = choice.finish_reason
        log(f"  finish_reason = {finish_reason}")

        # 2a. Tool calls requested. (A few servers send "stop" together with tool_calls,
        #     so we also look at message.tool_calls itself.)
        if finish_reason == "tool_calls" or message.tool_calls:
            if finish_reason != "tool_calls":
                log(f"  NOTE: provider sent finish_reason='{finish_reason}' but included tool calls; handling them.")

            tool_calls = message.tool_calls
            if len(tool_calls) > 1:
                stats["parallel"] = True
                log(f"  Model requested {len(tool_calls)} tool calls in ONE response (parallel).")

            # The assistant message (with its tool_calls) must be added to the history first.
            messages.append({
                "role": "assistant",
                "content": message.content or "",   # content is often empty when a tool is requested
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in tool_calls
                ],
            })

            # Handle EVERY tool call and answer EVERY tool_call_id.
            for call in tool_calls:
                tool_name = call.function.name
                raw_arguments = call.function.arguments
                log(f"  Tool call: {tool_name}  id={call.id}")
                log(f"    arguments (raw): {raw_arguments}")

                # Repeated identical call detection
                times_seen = register_call(seen_calls, tool_name, raw_arguments)
                if times_seen > MAX_IDENTICAL_CALLS:
                    answer = (
                        f"Stopped: the model repeated the identical call to '{tool_name}' "
                        f"{times_seen} times. Stopping to avoid an endless loop."
                    )
                    log(f"  {answer}")
                    print_summary(stats, answer)
                    return answer

                result = handle_tool_call(tool_name, raw_arguments)
                stats["tool_calls"].append(tool_name)

                # Failures are also sent back as normal tool messages (as strings).
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

            continue  # go back to the model with the tool results

        # 2b. Normal final answer
        if finish_reason == "stop":
            answer = message.content or ""
            log(f"\n  FINAL ANSWER: {answer}")
            print_summary(stats, answer)
            return answer

        # 2c. Still truncated after all retries
        if finish_reason == "length":
            answer = f"Stopped: the reply was still cut off after {MAX_LENGTH_RETRIES} retries. Partial text: {message.content}"
            log(f"  {answer}")
            print_summary(stats, answer)
            return answer

        # 2d. Anything else (for example "content_filter")
        answer = f"Stopped: unexpected finish_reason '{finish_reason}'."
        log(f"  {answer}")
        print_summary(stats, answer)
        return answer

    answer = f"Stopped: reached the maximum of {MAX_STEPS} agent steps without a final answer."
    log(f"\n  {answer}")
    print_summary(stats, answer)
    return answer


def main() -> None:
    client = create_client()

    if len(sys.argv) > 1:
        argument = sys.argv[1]
        if argument.isdigit() and int(argument) in QUESTIONS:
            questions = [QUESTIONS[int(argument)]]
        else:
            questions = [" ".join(sys.argv[1:])]
    else:
        questions = list(QUESTIONS.values())

    for question in questions:
        log("\n" + "=" * 70)
        log(f"QUESTION: {question}")
        log("=" * 70)
        try:
            run_agent(client, question)
        except APIError as err:
            # Network problems, wrong key, provider rejecting the request, etc.
            log(f"\n  API ERROR (the provider returned an error): {err}")


if __name__ == "__main__":
    main()