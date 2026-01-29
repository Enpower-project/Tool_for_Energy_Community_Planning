from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.models.schemas.alternatives import AlternativesIn, TechnologiesIn
from api.services import alternatives as alternatives_service
from api.dependencies import get_database

router = APIRouter(prefix="/alternatives", tags=["Alternatives"])

@router.post("/technologies", status_code=201)
async def generate_technologies_alternatives(
    input_data: TechnologiesIn
):
    return alternatives_service.technologies_alternatives(input_data=input_data)

@router.post("", status_code=201)
async def create_alternative(
    input_data: AlternativesIn,
    db: Session = Depends(get_database)
):
    return alternatives_service.create_alternative(input_data=input_data, db=db)