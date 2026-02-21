from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import shutil
import os
from models import process_user_audio

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "/home/temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

latest_link = None


# ✅ Serve Frontend
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ✅ Main API
@app.post("/schedule_meeting")
async def schedule(file: UploadFile = File(...)):
    global latest_link

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = process_user_audio(file_path)

    if result.get("status") == "completed":
        latest_link = result["calendar_link"]

    return result


@app.get("/success")
def success():
    if latest_link:
        return {
            "status": "successfully scheduled",
            "calendar_link": latest_link
        }

    return {"status": "no meeting scheduled"}
