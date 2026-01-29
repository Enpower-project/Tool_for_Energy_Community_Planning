from typing import Optional
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, field_validator

from api.models.schemas.demand_profile import DemandProfile


class BuildingIn(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    geom: Optional[str]
    height: float
    construction_year: int
    building_use_id: int
    area_conditioned: float
    demandprofile_id: Optional[int]
    subdivision_community: Optional[int]
    subdivision_total: Optional[int]
    occupants: Optional[int]
    demandprofile: Optional[DemandProfile] = None


class BuildingOut(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    geom: Optional[object]
    height: float
    construction_year: int
    building_use_id: int
    area_conditioned: float
    demandprofile_id: Optional[int]
    subdivision_community: Optional[int]
    subdivision_total: Optional[int]
    occupants: Optional[int]
    demandprofile: Optional[DemandProfile]

    @field_validator("geom")
    @classmethod
    def geom_transform(cls, v: WKBElement):
        if v is not None and type(v) == WKBElement:
            return str(to_shape(v).wkt)
        else:
            return None
