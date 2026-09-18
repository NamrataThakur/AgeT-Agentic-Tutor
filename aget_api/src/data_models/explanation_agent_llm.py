from typing import List, Dict
from pydantic import BaseModel, Field

class ExplanationAgentLLM(BaseModel):
    explanation : str = Field(description="The complete explanation tailored to the candidate's latest answer.")
    key_points_addressed : List[str] = Field( description=(
                                                "The exact reference key points addressed by the explanation. "
                                                "Each value must be copied exactly from the supplied reference key points."
                                            )
                                        )
    concepts_addressed : List[str] = Field(description=(
                                            "The concepts addressed by the explanation. "
                                            "Each concept must be from the supplied primary or secondary concepts."
                                        )
                                    )

