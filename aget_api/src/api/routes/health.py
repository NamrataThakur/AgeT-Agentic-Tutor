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


router = APIRouter(prefix="/health", tags=["health"])

@router.get("/health")
async def health():

    return {
        "status": "ok"
    }