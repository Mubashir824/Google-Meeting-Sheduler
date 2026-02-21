
import os
from elevenlabs import ElevenLabs
import re
import json
import re
from datetime import datetime, timedelta
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# ---------------- CONFIG ---------------- #

import os
from dotenv import load_dotenv
from google import genai
load_dotenv()  # MUST be before getenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=api_key)
ElevenLab = ElevenLabs(api_key=os.getenv("ELEVENLAB_API_KEY"))



SCOPES = ['https://www.googleapis.com/auth/calendar.events']

conversation_state = {
    "name": None,
    "date": None,
    "time": None,
    "title": None,
    "awaiting_confirmation": False,
    "confirmed": False,
    "calendar_link": None,
}

questions = [
    "What is your name?",
    "What date would you like to schedule the meeting?",
    "What time?",
    "Do you want to give a title for the meeting?"
]

def next_question(state: dict):
    if state["name"] is None:
        return questions[0]
    if state["date"] is None:
        return questions[1]
    if state["time"] is None:
        return questions[2]
    if state["title"] is None:
        return questions[3]
    return None
# ---------------- GOOGLE CALENDAR ---------------- #

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def google_calendar_service():
    # 1. Define the scopes (must match what you used to generate the token)
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']

    # 2. Reconstruct the credentials from Azure Environment Variables
    # These names must match the "Name" column in your Azure App Settings
    creds_data = {
        "token": os.getenv("token"),
        "refresh_token": os.getenv("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": os.getenv("client_id"),
        "client_secret": os.getenv("client_secret"),
        "scopes": SCOPES,
        "universe_domain": "googleapis.com"
    }

    # 3. Create the credentials object
    # This replaces Credentials.from_authorized_user_file('token.json')
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    # 4. (Optional) Auto-refresh the token if it has expired
    if creds and creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())

    # 5. Build and return the service
    return build('calendar', 'v3', credentials=creds)
    
# ---------------- LOGIC ---------------- #


import subprocess

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    response = ElevenLab.speech_to_text.convert(
        file=audio_bytes,
        model_id="scribe_v1"
    )

    return response.text

def parse_with_gemini(full_text: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    prompt = f"""
        Today is {today} (UTC).

        You are a STRICT information extraction system.

        Extract ONLY the clean values for these fields from the text below:
        - name (only the name, remove words like "my name is", "i am", "this is")
        - date (YYYY-MM-DD, convert relative dates using today's date)
        - time (HH:MM 24-hour, e.g. "5 pm" -> "17:00")
        - title (meeting purpose only; if user just says "meeting", keep it as "Meeting")

        Text:
        "{full_text}"

        Rules:
        - Return ONLY the extracted value, not the full sentence.
        - If a field is missing or unclear, return "" (empty string).
        - Do NOT guess missing values.
        - Output MUST be valid JSON only.

        Return exactly this JSON schema:

        {{
        "name": "",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "title": ""
        }}
    """
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    raw = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(raw)
import uuid

# Store all sessions keyed by session_id
conversation_sessions = {}

def create_new_session():
    session_id = str(uuid.uuid4())
    conversation_sessions[session_id] = {
        "name": None,
        "date": None,
        "time": None,
        "title": None,
        "awaiting_confirmation": False,
        "confirmed": False,
        "calendar_link": None,
    }
    return session_id

def get_session(session_id):
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = {
            "name": None,
            "date": None,
            "time": None,
            "title": None,
            "awaiting_confirmation": False,
            "confirmed": False,
            "calendar_link": None,
        }
    return conversation_sessions[session_id]

def reset_conversation(session_id):
    if session_id in conversation_sessions:
        conversation_sessions[session_id] = {
            "name": None,
            "date": None,
            "time": None,
            "title": None,
            "awaiting_confirmation": False,
            "confirmed": False,
            "calendar_link": None,
        }
def convert_to_iso(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return dt.isoformat()

def create_calendar_event(summary, start_iso):
    service = google_calendar_service()
    end_dt = datetime.fromisoformat(start_iso) + timedelta(hours=1)

    event_body = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": "UTC"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
    }

    event = service.events().insert(
        calendarId='primary',
        body=event_body
    ).execute()

    return event["htmlLink"]

def reset_conversation():
    conversation_state["name"] = None
    conversation_state["date"] = None
    conversation_state["time"] = None
    conversation_state["title"] = None
    conversation_state["confirmed"] = False
    conversation_state["calendar_link"] = None
    conversation_state["awaiting_confirmation"] = False
    conversation_state.pop("parsed_data", None)
    
def prepare_confirmation():

    combined = (
        f"Name: {conversation_state['name']}. "
        f"Date: {conversation_state['date']}. "
        f"Time: {conversation_state['time']}. "
        f"Title: {conversation_state['title']}."
    )

    print("\n========== DEBUG START ==========")
    print("Combined Text Sent To Gemini:")
    print(combined)

    parsed = parse_with_gemini(combined)

    print("Gemini Parsed Output:", parsed)
    print("========== DEBUG END ==========\n")

    if not parsed.get("date") or not parsed.get("time"):
        reset_conversation()
        return {
            "status": "error",
            "message": "I could not understand the date or time. Restarting.",
            "next_question": questions[0]
        }

    conversation_state["parsed_data"] = parsed
    conversation_state["awaiting_confirmation"] = True

    summary = (
        f"Please confirm your meeting details. "
        f"Name: {parsed['name']}, "
        f"Date: {parsed['date']}, "
        f"Time: {parsed['time']}, "
        f"Title: {parsed['title']}. "
        f"Say yes to confirm or no to restart."
    )

    return {
        "status": "confirm",
        "message": summary
    }
def schedule_confirmed_meeting():

    parsed = conversation_state["parsed_data"]

    iso_time = convert_to_iso(parsed["date"], parsed["time"])
    title = parsed.get("title") or "Meeting"

    link = create_calendar_event(title, iso_time)

    conversation_state["confirmed"] = True
    conversation_state["calendar_link"] = link
    conversation_state["awaiting_confirmation"] = False

    return {
        "status": "completed",
        "calendar_link": link
    }    
def finalize_and_schedule():

    combined = (
        f"Name: {conversation_state['name']}. "
        f"Date: {conversation_state['date']}. "
        f"Time: {conversation_state['time']}. "
        f"Title: {conversation_state['title']}."
    )

    print("\n========== DEBUG START ==========")
    print("Combined Text Sent To Gemini:")
    print(combined)

    parsed = parse_with_gemini(combined)

    print("\nGemini Parsed Output:")
    print(parsed)
    print("========== DEBUG END ==========\n")

    # Validation
    if not parsed.get("date") or not parsed.get("time"):
        print("❌ Date or Time Missing After Gemini Parsing")
        return {
            "status": "error",
            "message": "I could not understand the date or time. Please try again.",
            "restart": True,
            "next_question": questions[0]
        }

    iso_time = convert_to_iso(parsed["date"], parsed["time"])

    title = parsed.get("title") or "Meeting"

    link = create_calendar_event(title, iso_time)

    conversation_state["confirmed"] = True
    conversation_state["calendar_link"] = link

    return {
        "status": "completed",
        "calendar_link": link,
        "details": parsed
    }
# ---------------- MAIN STEP FUNCTION ---------------- #

def process_user_audio(file_path: str):
    conversation_state = get_session(session_id)
    # If conversation finished previously, reset automatically
    if conversation_state.get("confirmed"):
        reset_conversation()
    user_text = transcribe_audio(file_path).strip().lower()
    print("User said:", user_text)
    
    if conversation_state.get("awaiting_confirmation"):
        clean = user_text.strip().lower()
        print("Confirmation response:", repr(clean))
    
        # If nothing detected → treat as YES
        if not clean:
            print("No text detected → Defaulting to YES")
            return schedule_confirmed_meeting()
    
        # Remove punctuation
        clean = re.sub(r"[^\w\s]", "", clean)
    
        yes_words = ["yes", "yeah", "yep", "confirm", "correct", "sure", "ok", "okay"]
        no_words = ["no", "nope", "cancel", "restart"]
    
        if any(word in clean for word in yes_words):
            return schedule_confirmed_meeting()
    
        elif any(word in clean for word in no_words):
            reset_conversation()
            return {"status": "restart", "next_question": questions[0]}
    
        # If unclear → default to YES
        print("Unclear response → Defaulting to YES")
        return schedule_confirmed_meeting()

        
    # Step-by-step state filling
    if conversation_state["name"] is None:
        conversation_state["name"] = user_text
        return {"status": "in_progress", "next_question": questions[1]}

    elif conversation_state["date"] is None:
        conversation_state["date"] = user_text
        return {"status": "in_progress", "next_question": questions[2]}

    elif conversation_state["time"] is None:
        conversation_state["time"] = user_text
        return {"status": "in_progress", "next_question": questions[3]}

    elif conversation_state["title"] is None:
        conversation_state["title"] = user_text or "Meeting"
        return prepare_confirmation()

    # Safety fallback

    return prepare_confirmation()






