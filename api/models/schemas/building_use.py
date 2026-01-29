from pydantic import BaseModel, ConfigDict


class BuildingUseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    sort: int
    icon: str
    name_translate: str
