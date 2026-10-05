from config import ATTENDANCE, LATE_FINE, MIN_ATTENDANCE


def workflow(question):

    question = question.lower()

    # Rule 1: Attendance lookup
    if "dsa" in question and "attendance" in question:
        return f"Your DSA attendance is {ATTENDANCE['DSA']}%."

    elif "german" in question and "attendance" in question:
        attendance = ATTENDANCE["German"]

        if "above 75" in question:
            if attendance > MIN_ATTENDANCE:
                return "Yes, your German attendance is above 75%."
            else:
                return "No, your German attendance is not above 75%."

        return f"Your German attendance is {attendance}%."

    # Rule 2: Average attendance
    elif "average" in question and "attendance" in question:
        total = sum(ATTENDANCE.values())
        average = total / len(ATTENDANCE)
        return f"Your average attendance is {average:.2f}%."

    # Rule 3: Late fine
    elif "3 late" in question and "fine" in question:
        return f"Your fine for 3 late days is Rs. {LATE_FINE[3]}."

    # Rule 4: Exam eligibility
    elif "exam" in question and "75" in question:
        eligible_subjects = []

        for subject, attendance in ATTENDANCE.items():
            if attendance >= MIN_ATTENDANCE:
                eligible_subjects.append(subject)

        return (
            "You meet the minimum 75% attendance requirement in: "
            + ", ".join(eligible_subjects)
            + "."
        )

    # No matching predefined rule
    else:
        return "Sorry, I do not have a predefined rule for this question."


if __name__ == "__main__":

    questions = [
        "What is my DSA attendance?",
        "Is my German attendance above 75%?",
        "Calculate my average attendance.",
        "If I have 3 late days, what is my fine?",
        "Can I attend the exam if minimum attendance is 75%?"
    ]

    for question in questions:
        print("Q:", question)
        print("A:", workflow(question))
        print("-" * 60)