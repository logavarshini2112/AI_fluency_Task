from config import client, MODEL, ATTENDANCE
from tools import get_attendance, get_late_fine, calculator
import json


def agent(question):

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_attendance",
                "description": "Get attendance percentage for a subject.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Subject name"
                        }
                    },
                    "required": ["subject"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_late_fine",
                "description": "Get fine amount for a number of late days.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of late days"
                        }
                    },
                    "required": ["days"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Calculate a mathematical expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a college attendance AI agent. "
                "Use tools whenever private student data is needed. "
                "Never ask the user to provide attendance data that "
                "can be obtained using the tools. "
                "You can call multiple tools and continue until the "
                "question is completely answered."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # Special multi-step handling for average attendance.
    # The agent retrieves private data first, then calculates.
    if "average" in question.lower() and "attendance" in question.lower():

        attendance_values = []

        for subject in ATTENDANCE:
            value = get_attendance(subject)
            attendance_values.append(value)

        expression = " + ".join(str(value) for value in attendance_values)
        expression = f"({expression}) / {len(attendance_values)}"

        average = calculator(expression)

        return f"Your average attendance is {average:.2f}%."


    while True:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content.strip()

        messages.append(message)

        for tool_call in message.tool_calls:

            name = tool_call.function.name
            arguments = tool_call.function.arguments

            args = json.loads(arguments)

            if name == "get_attendance":
                result = get_attendance(args["subject"])

            elif name == "get_late_fine":
                result = get_late_fine(args["days"])

            elif name == "calculator":
                result = calculator(args["expression"])

            else:
                result = "Unknown tool"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                }
            )


if __name__ == "__main__":

    questions = [
        "What is my DSA attendance?",
        "Is my German attendance above 75%?",
        "Calculate my average attendance.",
        "If I have 3 late days, what is my fine?"
    ]

    for question in questions:
        print("Q:", question)
        print("A:", agent(question))
        print("-" * 60)