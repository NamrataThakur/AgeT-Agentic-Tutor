from pathlib import Path
import uuid

from fastapi import APIRouter,UploadFile, File, Form, HTTPException

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from application.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview"])

interview_service = InterviewService()

# ---------------------------------------------------------
# Temporary audio directory
# ---------------------------------------------------------

TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/text")
async def process_text(user_id: str = Form(...), interview_id: str = Form(...),text: str = Form(...)):

    try:
        response = await interview_service.process_text(user_id=user_id,
                                                        interview_id=interview_id,
                                                        message=text)

        return {
            "user_id": user_id,
            "interview_id": interview_id,
            "response": str(response),
        }

    except Exception as e:
        print("Text processing failed : ",    repr(e))

        raise HTTPException(status_code=500, detail="Failed to process interview message")



@router.post("/audio")
async def process_audio(user_id: str = Form(...),interview_id: str = Form(...),audio: UploadFile = File(...)):

    return