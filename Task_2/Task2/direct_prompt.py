"""Day 2 Task: Direct Prompting"""

from config import client, MODEL

QUESTION = (
    "A student has 82% attendance in DSA, 71% in German, "
    "and 91% in Python. What is the average attendance?"
)

PROMPT = (
    "You are a helpful college assistant. "
    "Give only the final answer. Do not explain."
)


def ask(question):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print("=== DIRECT PROMPTING ===")
    print("QUESTION:", QUESTION)
    print("\nANSWER:", ask(QUESTION))