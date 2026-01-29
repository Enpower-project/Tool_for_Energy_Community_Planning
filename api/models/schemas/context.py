from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import date

from api.models.schemas.building_asset_context import (
    BuildingAssetContextIn,
    BuildingAssetContextOut,
)


class ContextIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = None
    start_date: date = date.today()
    timestep_count: int = 8760
    timestep_duration: int = 3600000
    author: str = "id_keycloak_here"
    creation_date: date = date.today()
    description: str = None
    context_parent: Optional[int] = None
    building_asset_context: List[BuildingAssetContextIn]


class ContextOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    timestep_count: int
    timestep_duration: int
    author: str
    creation_date: date
    description: str
    context_parent: Optional[int] = None
    building_asset_context: List[BuildingAssetContextOut]


class ContextListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    timestep_count: int
    timestep_duration: int
    author: str
    creation_date: date
    description: str
    context_parent: Optional[int] = None
    geom: Optional[object]

    @field_validator("geom")
    @classmethod
    def geom_transform(cls, v: WKBElement):
        if v is not None and type(v) == WKBElement:
            return str(to_shape(v).wkt)
        else:
            return None
