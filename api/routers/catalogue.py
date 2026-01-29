from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_database
from api.models.schemas.building_use import BuildingUseOut
from api.services import catalogue as catalogue_service

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.get("/building-use", response_model=List[BuildingUseOut])
async def get_building_use_list(
    db: Session = Depends(get_database),
) -> List[BuildingUseOut]:
    return catalogue_service.get_building_use_list(db=db)
