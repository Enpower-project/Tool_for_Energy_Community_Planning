from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, status

from api.models.schemas.alternatives import AlternativesIn, TechnologiesIn
from api.services.scripts.module_integration import generate_resbased_generator_list_technologies, get_new_context
from api.services.context import get_context

def technologies_alternatives(input_data: TechnologiesIn):
    return generate_resbased_generator_list_technologies(front_data=input_data.model_dump())

def create_alternative(input_data: AlternativesIn, db: Session):
    context = jsonable_encoder(get_context(id=input_data.context_id,db= db)["context"])
    recommendations = {k: v.model_dump() for k, v in input_data.recommendations.items()}
    try:
        return get_new_context(goal=2, community_context=context,recommendations_dic=recommendations)
    except Exception as ex:
        print(ex)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=repr(ex),
        )