from pydantic import Field, BaseModel
from typing import List

class ConceptClassify(BaseModel):
    primary_concept : str
    secondary_concepts : List[str] | None