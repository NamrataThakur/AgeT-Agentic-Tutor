
from fastapi import Request

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.container.application_container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    container = request.app.state.container
    return container