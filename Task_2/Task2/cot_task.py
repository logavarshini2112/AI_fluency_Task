"""Day 2 Task: Chain-of-Thought Prompting"""

from config import client, MODEL

QUESTION = (
    "A student has 82% attendance in DSA, 71% in German, "
    "and 91% in Python. What is the average attendance?"
)

PROMPT = (
    "You are a helpful college assistant. "
    "Solve the problem step by step and then give the final answer."
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
    print("=== CHAIN-OF-THOUGHT PROMPTING ===")
    print("QUESTION:", QUESTION)
    print("\nANSWER:")
    print(ask(QUESTION))