from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from api.database import SessionLocal
from api.models.schemas.token_data import TokenData
from api.constants import (
    KEYCLOAK_AUTH_URL, 
    KEYCLOAK_CLIENT_ID_BACK,
    KEYCLOAK_REALM_ID, 
    KEYCLOAK_SECRET_KEY_BACK, 
    KEYCLOAK_TOKEN_AUTH_URL
)

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=KEYCLOAK_TOKEN_AUTH_URL)

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_AUTH_URL,
    client_id=KEYCLOAK_CLIENT_ID_BACK,
    realm_name=KEYCLOAK_REALM_ID,
    client_secret_key=KEYCLOAK_SECRET_KEY_BACK,
    verify=True,
)

credential_exception = HTTPException(
    status_code= status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
)

def get_query_token(token:str = Depends(oauth2_scheme)):
    return TokenData.model_validate(keycloak_openid.introspect(token))

def authorization(token: TokenData = Depends(get_query_token)): 
    if token is None:
        raise credential_exception
    
    if token.active == False:
        raise credential_exception
    
    return token