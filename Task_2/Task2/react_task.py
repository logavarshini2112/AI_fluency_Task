"""Day 2 Task: ReAct Prompting with Tools"""

from config import client, MODEL
from tools import get_attendance, get_fine


QUESTION = (
    "For student ST101, what is the attendance percentage and fine amount?"
)


def ask_react(question):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a college assistant using a ReAct-style approach. "
                "When external student information is needed, use the available tools. "
                "Think about what information is needed, take an action using a tool, "
                "observe the result, and then give the final answer."
            ),
        },
        {"role": "user", "content": question},
    ]

    attendance = get_attendance("ST101")
    print(f"Thought: I need the attendance for student ST101.")
    print(f"Action: get_attendance('ST101')")
    print(f"Observation: {attendance}")

    fine = get_fine("ST101")
    print(f"Thought: I also need the fine amount for student ST101.")
    print(f"Action: get_fine('ST101')")
    print(f"Observation: {fine}")

    final_prompt = (
        f"Student ST101 has {attendance}% attendance and a fine of Rs. {fine}. "
        "Give a concise final answer."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Give a concise final answer."},
            {"role": "user", "content": final_prompt},
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print("=== REACT PROMPTING ===")
    print("QUESTION:", QUESTION)
    print("\n--- ReAct Trace ---")

    answer = ask_react(QUESTION)

    print("\nFINAL ANSWER:", answer)