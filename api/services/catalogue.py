from typing import List
from sqlalchemy.orm import Session

from api.models.models import BuildingUse


def get_building_use_list(db: Session) -> List[BuildingUse]:
    return db.query(BuildingUse).order_by(BuildingUse.sort).all()
