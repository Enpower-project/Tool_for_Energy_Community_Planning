from typing import List, Optional
from pydantic import BaseModel

class Roles(BaseModel):
    roles: Optional[List[str]] = None

class TokenData(BaseModel):
    sid: Optional[str] = None
    sub: Optional[str] = None
    preferred_username: Optional[str] = None
    active: bool = False
    scope: Optional[str] = None
    realm_access: Roles = None
    groups: Optional[List[str]] = None
