from config import ATTENDANCE, LATE_FINE, MIN_ATTENDANCE


def get_attendance(subject):
    subject = subject.strip()

    for name, attendance in ATTENDANCE.items():
        if name.lower() == subject.lower():
            return attendance

    return None


def get_late_fine(days):
    return LATE_FINE.get(days)


def calculator(expression):
    allowed = "0123456789+-*/(). "

    if not all(char in allowed for char in expression):
        raise ValueError("Invalid expression")

    return eval(expression, {"__builtins__": {}}, {})


if __name__ == "__main__":

    print("DSA attendance:", get_attendance("DSA"))
    print("German attendance:", get_attendance("German"))
    print("3-day fine:", get_late_fine(3))
    print("Average:", calculator("(85 + 78 + 92 + 74) / 4"))