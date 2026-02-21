# Voice Scheduling Agent (Deployed)

## Overview

A real-time AI-powered voice assistant that schedules meetings directly
into Google Calendar through natural speech interaction.

The assistant: - Initiates a voice conversation - Collects user's name,
preferred date, time, and optional meeting title - Confirms the
details - Creates a real Google Calendar event - Returns the calendar
event link

------------------------------------------------------------------------

## Live Demo

Deployed URL: [https://your-deployed-url.com](https://mubashir-hshje0fgcyeehjdz.centralindia-01.azurewebsites.net)

### How to Test

1.  Open the deployed link.
2.  Click **Start Scheduling**.
3.  Allow microphone access.
4.  Respond to the prompts (name, date, time, title).
5.  Confirm by saying **Yes**.
6.  A real Google Calendar event will be created.

------------------------------------------------------------------------

## Tech Stack

Frontend: - HTML - JavaScript (MediaRecorder API, SpeechSynthesis API)

Backend: - Python - FastAPI - Whisper (Speech-to-Text)

Integration: - Google Calendar API - OAuth 2.0 Authentication

Deployment: - Render / Railway / Cloud VM (update accordingly)

------------------------------------------------------------------------

## System Architecture

1.  Browser captures voice input.
2.  Audio sent to backend.
3.  Whisper converts speech to text.
4.  Conversation state logic processes inputs.
5.  Confirmation step ensures accuracy.
6.  Google Calendar API creates the event.
7.  Event link returned to user.

------------------------------------------------------------------------

## Calendar Integration Explanation

-   Uses Google Calendar API (calendar.v3).
-   OAuth 2.0 authentication flow.
-   Access tokens stored securely.
-   Creates event with:
    -   Title (summary)
    -   Start time (ISO format)
    -   End time (1-hour duration)
    -   Timezone (UTC)

------------------------------------------------------------------------

## Running Locally

Clone repository:

    git clone https://github.com/Mubashir824/Google-Meeting-Sheduler.git
    cd Google-Meeting-Sheduler

Install dependencies:

    pip install -r requirements.txt

Run server:

    uvicorn app:app
    
Open in browser:

    http://127.0.0.1:8000

------------------------------------------------------------------------

## Project Structure

app.py \# FastAPI server models.py \# Conversation logic
templates/index.html \# Voice interface temp/ \# Temporary audio storage

------------------------------------------------------------------------

## Demo Evidence

Include: - Screenshot of interaction - Screenshot of confirmation -
Screenshot of created calendar event - Loom demo link
