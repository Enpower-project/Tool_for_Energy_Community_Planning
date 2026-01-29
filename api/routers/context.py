from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import authorization, get_database
from api.models.schemas.context import ContextIn, ContextListOut, ContextOut
from api.models.schemas.token_data import TokenData
from api.services import context as context_service

router = APIRouter(prefix="/context", tags=["Context"])


@router.post("", status_code=201, response_model=ContextOut)
async def create_context(
    input_data: ContextIn,
    db: Session = Depends(get_database),
    token:TokenData = Depends(authorization)
) -> ContextOut:
    user_id = token.sub
    return context_service.create_baseline(input_data=input_data, db=db, author=user_id)


@router.get("", response_model=List[ContextListOut])
async def get_context_list(
    db: Session = Depends(get_database),
) -> List[ContextListOut]:
    return context_service.get_baseline_context_list(db=db)

@router.get("/{id}", response_model=ContextOut)
async def get_context_by_id(
    id: int,
    db: Session = Depends(get_database),
) -> ContextOut:
    return context_service.get_baseline_by_id_context(id=id, db=db)

@router.get("/data/{id}")
async def get_context_by_id(
    id: int,
    db: Session = Depends(get_database),
):
    return context_service.get_context(id=id, db=db)

@router.delete("/{id}",  status_code=202)
async def delete_context_by_id(
    id: int,
    db: Session = Depends(get_database),
    token:TokenData = Depends(authorization)
) -> ContextOut:
    user_id = token.sub
    return context_service.delete_baseline_by_id_context(id=id, db=db, author=user_id)

@router.put("/{id}",  response_model=ContextOut)
async def rename_context(
    name: str,
    id: int,
    db: Session = Depends(get_database),
    token:TokenData = Depends(authorization)
) -> ContextOut:
    user_id = token.sub
    return context_service.rename_context_by_id(id=id, db=db, author=user_id, name=name)

@router.get("/{id}/alternatives",response_model=List[ContextListOut])
async def get_context_list(
    id: int,
    db: Session = Depends(get_database),
) -> List[ContextListOut]:
    return context_service.get_alternatives_list(id=id, db=db)