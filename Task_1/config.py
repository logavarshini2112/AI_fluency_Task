import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "groq").strip().lower()
MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")

if PROVIDER == "groq":
    BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY = os.getenv("GROQ_API_KEY")
else:
    raise SystemExit("This task uses Groq. Check your .env file.")

if not API_KEY:
    raise SystemExit("GROQ_API_KEY not found. Check your .env file.")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

# Private student data
ATTENDANCE = {
    "Python": 85,
    "DBMS": 78,
    "DSA": 92,
    "German": 74
}

LATE_FINE = {
    1: 50,
    2: 100,
    3: 150
}

MIN_ATTENDANCE = 75