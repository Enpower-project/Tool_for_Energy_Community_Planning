from typing import List, Optional
from pydantic import BaseModel, Field


class BasicBaselineIn(BaseModel):
    location: str = Field(examples=["POINT(-3.703790 40.416775)"])
    num_building: int = Field(examples=["3"])
    building_use_id: int = Field(examples=["1"])


class DwellingsIn(BaseModel):
    building_use_id: int = Field(examples=["1"])
    adults_working_out_of_home: int = Field(examples=["0"])
    adults_working_remotely: int = Field(examples=["0"])
    adults_unemployed: int = Field(examples=["0"])
    students_working: int = Field(examples=["0"])
    students_unemployed: int = Field(examples=["0"])
    children: int = Field(examples=["0"])
    retired_people: int = Field(examples=["0"])
    farm: bool = Field(examples=["true"])

class IntermediateBaselineIn(BaseModel):
    geom: str = Field(
        examples=[
            "POLYGON ((-4.729664 41.656342, -4.7297184 41.65631, -4.7296618 41.6562566, -4.7296117 41.656278, -4.7295978 41.6562844, -4.729664 41.656342))"
        ]
    )
    construction_year: int = Field(examples=["2010"])
    subdivision_community: Optional[int] = Field(...,examples=["1"])
    subdivision_total: Optional[int] = Field(...,examples=["1"])
    occupants: int = Field(examples=["3"])
    building_type_id: int = Field(examples=["1"])
    building_statistics_profile_id: Optional[int] = None
    name: str
    dwellings: List[DwellingsIn]

class IntermediateBaseline(BaseModel):
    geom: str
    construction_year: int
    subdivision_community: Optional[int]
    subdivision_total: Optional[int]
    occupants: int
    building_type_id: int
    building_statistics_profile_id: Optional[int]=None
    name: str
    building_use_id: int
    adults_working_out_of_home: int
    adults_working_remotely: int
    adults_unemployed: int
    students_working: int
    students_unemployed: int
    children: int
    retired_people: int
    farm: bool