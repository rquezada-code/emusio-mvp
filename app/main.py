from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os
import requests

from dotenv import load_dotenv
from openai import OpenAI


# ======================
# App setup
# ======================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(
    title="Emusio AI Practice Coach",
    description="AI coach that generates a short daily music practice plan",
    version="0.2.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ======================
# Models
# ======================

class PracticeRequest(BaseModel):
    teacher_notes: Optional[str] = None
    lesson_id: Optional[str] = None


class PracticeResponse(BaseModel):
    practice_plan: str


# ======================
# Phase 0 mock lessons
# ======================

MOCK_LESSONS = {
    "violin_demo": """
Worked on B major scale, focusing on intonation and relaxed left-hand fingers.
Reviewed string crossings and consistent bow speed.
Short section of the piece was practiced slowly for accuracy.
""",
    "piano_demo": """
Practiced G major scale hands separately, focusing on even rhythm.
Worked on two short pieces, paying attention to dynamics and articulation.
Reviewed posture and relaxed wrists.
""",
    "demo": """
Practiced major scales slowly, focusing on clean transitions and steady rhythm.
Worked on musical phrasing and relaxed technique.
"""
}


# ======================
# Routes
# ======================

@app.get("/")
def root():
    return RedirectResponse(url="/practice-coach-ui")

@app.get("/health")
def health():
    return {"message": "Emusio AI Practice Coach is running 🎵"}

@app.get("/emusio-app-mock")
def emusio_app_mock(request: Request):
    return templates.TemplateResponse(
        "emusio_app_mock/index.html",
        {"request": request}
    )

# ======================
# Fake Emusio Lesson API
# ======================

@app.get("/api/lesson/{lesson_id}")
def get_lesson(lesson_id: str):
    lesson = MOCK_LESSONS.get(lesson_id)

    if not lesson:
        return {"error": "Lesson not found"}

    # 🔥 Detect instrument from lesson_id
    if "violin" in lesson_id:
        instrument = "violin"
    elif "piano" in lesson_id:
        instrument = "piano"
    else:
        instrument = "unknown"

    return {
        "lesson_id": lesson_id,
        "student_id": "student_001",
        "instrument": instrument,
        "transcription": lesson
    }

@app.post("/practice-coach", response_model=PracticeResponse)
def practice_coach(request: PracticeRequest):

    # 1️⃣ Resolve lesson notes via API (simulated Emusio integration)
    if request.lesson_id:

        api_response = requests.get(
            f"http://localhost:8000/api/lesson/{request.lesson_id}"
        )

        if api_response.status_code != 200:
            return {
                "practice_plan": f"No lesson found for lesson_id: {request.lesson_id}"
            }

        lesson_data = api_response.json()

        if "error" in lesson_data:
            return {
                "practice_plan": f"No lesson found for lesson_id: {request.lesson_id}"
            }

        teacher_notes = lesson_data.get("transcription")
        instrument = lesson_data.get("instrument")

    else:
        teacher_notes = request.teacher_notes
        instrument = "unknown"

    if not teacher_notes:
        return {"practice_plan": "No lesson data provided."}

    # 2️⃣ Build prompt
    prompt = f"""
    You are an encouraging AI music practice coach inside the Emusio app.

    Instrument: {instrument}

    Based on the following lesson transcription, generate a structured and motivating practice plan for today.

    IMPORTANT INSTRUCTIONS:

    - Identify the instrument from the lesson context.
    - Create a clear, visually structured plan.
    - Use short sections with headings.
    - Use bullet points for clarity.
    - Keep it concise and student-friendly.
    - Tone should be positive, supportive, and motivating.
    - Avoid long paragraphs.
    - Include an estimated total practice time at the end.
    - Format the output in clean Markdown.

    Structure the output exactly like this:

    ## 🎵 Your Practice Plan for Today

    ### 🔥 Warm-Up (1–3 minutes)
    - ...

    ### 🎯 Focus Practice (3–5 minutes)
    - ...

    ### 🎼 Musical Play / Review (1–3 minutes)
    - ...

    ### 🌟 Coach Tip
    Short encouraging message.

    ### ⏱ Estimated Total Time
    X–Y minutes

    Lesson Transcription:
    {teacher_notes}
    """

    # 3️⃣ Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional music practice coach."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
    )

    practice_plan = response.choices[0].message.content.strip()

    return {"practice_plan": practice_plan}


# ======================
# Frontend
# ======================

@app.get("/practice-coach-ui", response_class=HTMLResponse)
def practice_coach_ui(request: Request):
    lesson_id = request.query_params.get("lesson_id")

    return templates.TemplateResponse(
        "practice_coach.html",
        {
            "request": request,
            "lesson_id": lesson_id
        }
    )
