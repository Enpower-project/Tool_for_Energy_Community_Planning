from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_database
from api.models.schemas.baseline import BasicBaselineIn, IntermediateBaselineIn
from api.services import baseline as baseline_service

router = APIRouter(prefix="/baseline", tags=["Baseline"])


@router.post("/basic", status_code=201)
async def generate_basic_baseline(
    input_data: BasicBaselineIn, db: Session = Depends(get_database)
):
    return baseline_service.basic_baseline(input_data=input_data, db=db)

@router.post("/basic/data", status_code=201)
async def generate_basic_baseline_data(
    input_data: BasicBaselineIn, db: Session = Depends(get_database)
):
    return baseline_service.basic_baseline_data(input_data=input_data, db=db)


@router.post("/intermediate", status_code=201)
async def generate_intermediate_baseline(
    input_data: List[IntermediateBaselineIn], db: Session = Depends(get_database)
):
    return baseline_service.intermediate_baseline(front_data=input_data, db=db)


@router.post("/intermediate/data", status_code=201)
async def generate_intermediate_baseline_data(
    input_data: List[IntermediateBaselineIn], db: Session = Depends(get_database)
):
    return baseline_service.intermediate_baseline_data(input_data=input_data, db=db)
