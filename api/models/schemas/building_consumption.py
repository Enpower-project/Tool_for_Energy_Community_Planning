from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class BuildingConsumption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    elec_consumption: Optional[List[float|None]] = None
    heat_consumption: Optional[List[float|None]] = None
    cool_consumption: Optional[List[float|None]] = None
    dhw_consumption: Optional[List[float|None]] = None
