from fastapi import FastAPI
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.routes import interview
from api.routes import health

app = FastAPI(title="AgeT FastAPI Backend Service", version="1.0.0")

app.include_router(router=interview.router)
app.include_router(router=health.router)

