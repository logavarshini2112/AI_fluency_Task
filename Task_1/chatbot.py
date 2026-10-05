from config import client, MODEL


def chatbot(question):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a simple college chatbot. "
                    "Answer the user's question using only your general knowledge. "
                    "You do not have access to private student attendance data."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":

    questions = [
        "What is my DSA attendance?",
        "Is my German attendance above 75%?",
        "Write a short message encouraging students to maintain good attendance."
    ]

    for question in questions:
        print("Q:", question)
        print("A:", chatbot(question))
        print("-" * 60)