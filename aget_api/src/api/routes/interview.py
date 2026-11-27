from pathlib import Path
import uuid
from pydantic import BaseModel

from fastapi import APIRouter,UploadFile, File, Form, HTTPException, Request, Depends

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.container.application_container import ApplicationContainer
from api.dependency import get_container

router = APIRouter(prefix="/interview", tags=["interview"])

# ---------------------------------------------------------
# Temporary audio directory
# ---------------------------------------------------------

TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class StartInterviewRequest(BaseModel):

    interview_id: str
    user_input: str | None = None
    user_id: str
    user_audio : str | None = None
    

@router.post("/text")
async def process_text(payload : StartInterviewRequest, 
                       container : ApplicationContainer = Depends(get_container)):

    
    try:
        response = await container.interview_service.process_text(user_id=payload.user_id,
                                                        interview_id=payload.interview_id,
                                                        message=payload.user_input)

        return {
            "user_id": payload.user_id,
            "interview_id": payload.interview_id,
            "response": str(response),
        }

    except Exception as e:
        print("Text processing failed : ", repr(e))

        raise HTTPException(status_code=500, detail="Failed to process interview message using text input")



@router.post("/audio")
async def process_audio(payload : StartInterviewRequest,
                        container : ApplicationContainer = Depends(get_container)):

    try:
        response = await container.interview_service.process_audio(user_id=payload.user_id,
                                                         interview_id=payload.interview_id,
                                                         audio_path=payload.user_audio)

        return {
            "user_id": payload.user_id,
            "interview_id": payload.interview_id,
            "response": str(response),
        }

    except Exception as e:
        print("Audio processing failed : ", repr(e))
        
        raise HTTPException(status_code=500, detail="Failed to process interview message using audio input")

    



@router.post("/resume")
async def resume_interview(payload : StartInterviewRequest,
                           container : ApplicationContainer = Depends(get_container)):
    try:
        response = await container.interview_service.resume_interview(user_id=payload.user_id,
                                                            interview_id=payload.interview_id,
                                                            message=payload.user_input)

        return {
            "user_id": payload.user_id,
            "interview_id": payload.interview_id,
            "response": str(response),
        }

    except Exception as e:
        print("Text processing failed : ", repr(e))

        raise HTTPException(status_code=500, detail="Failed to process interview message using text input")
    

