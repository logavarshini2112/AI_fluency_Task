"""Day 2 Task: Self-Consistency Experiment"""

from config import client, MODEL

QUESTION = (
    "A student has 82% attendance in DSA, 71% in German, "
    "and 91% in Python. What is the average attendance?"
)


def ask(question, temperature):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Solve the problem carefully. "
                    "Give the final numerical answer clearly."
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print("=== SELF-CONSISTENCY EXPERIMENT ===")
    print("QUESTION:", QUESTION)

    print("\n--- Temperature 0.8: 5 runs ---")

    for i in range(1, 6):
        answer = ask(QUESTION, 0.8)
        print(f"\nRun {i}:")
        print(answer)

    print("\n--- Temperature 0: deterministic run ---")
    answer = ask(QUESTION, 0)
    print("\nTemperature 0 answer:")
    print(answer)