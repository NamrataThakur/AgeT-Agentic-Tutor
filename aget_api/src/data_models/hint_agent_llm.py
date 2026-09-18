from typing import List, Dict
from pydantic import BaseModel, Field

class HintAgentLLM(BaseModel):
    hint : str
    target_key_point : str

