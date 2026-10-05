def get_attendance(student_id):
    attendance_data = {
        "ST101": 68,
        "ST102": 82,
        "ST103": 74,
    }

    return attendance_data.get(student_id, "Student not found")


def get_fine(student_id):
    fine_data = {
        "ST101": 150,
        "ST102": 0,
        "ST103": 50,
    }

    return fine_data.get(student_id, "Student not found")


def calculator(expression):
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {e}"