from typing import List
from pydantic import BaseModel


class DemandProfile(BaseModel):
    heating_demand: List[float]
    cooling_demand: List[float]
    dhw_demand: List[float]
    electricity_demand: List[float]
