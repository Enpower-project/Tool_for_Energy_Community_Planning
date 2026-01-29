from pydantic import BaseModel, Field
from typing import Dict

class TechnologiesIn(BaseModel):
    goals: str = Field(examples=["3"])
    country: str = Field(examples=["AT"])

class Reccommendation(BaseModel):
    id: int
    action_name: str

class AlternativesIn(BaseModel):
    context_id: int
    recommendations: Dict[int, Reccommendation]