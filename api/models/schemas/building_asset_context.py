from pydantic import BaseModel, ConfigDict
from typing import Optional

from api.models.schemas.building import BuildingIn, BuildingOut
from api.models.schemas.building_consumption import BuildingConsumption


class BuildingAssetContextIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generation_system_profile_id: Optional[int]
    building_consumption: Optional[BuildingConsumption]
    building: Optional[BuildingIn]
    name: Optional[str]


class BuildingAssetContextOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int]
    generation_system_profile_id: Optional[int]
    building_consumption: Optional[BuildingConsumption]
    building: Optional[BuildingOut]
    name: Optional[str]
