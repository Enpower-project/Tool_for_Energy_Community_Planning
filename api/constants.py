from os import getenv
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

# API VERSION
API_VERSION="0.1.0"

# CORS_ORIGINS
CORS_ORIGINS = getenv("CORS_ORIGINS").split(",")
EXTERNAL_ROOT_PATH = getenv("EXTERNAL_ROOT_PATH")

# DATABASE
SQLALCHEMY_DATABASE_URL = URL.create(
    drivername="postgresql",
    host=getenv("DB_HOST"),
    database=getenv("DB_DATABASE"),
    username=getenv("DB_USER"),
    password=getenv("DB_PASSWORD"),
)

# GIS
SRID=4326

# THERMAGRID API
THERMAGRID_API_URL = getenv("THERMAGRID_API_URL")
THERMAGRID_API_KEY = getenv("THERMAGRID_API_KEY")

# KEYCLOAK
KEYCLOAK_REALM_ID = getenv("KEYCLOAK_REALM_ID")
KEYCLOAK_CLIENT_ID_BACK = getenv("KEYCLOAK_CLIENT_ID_BACK")
KEYCLOAK_SECRET_KEY_BACK = getenv("KEYCLOAK_SECRET_KEY_BACK")
KEYCLOAK_BASE_URL = getenv("KEYCLOAK_BASE_URL")
KEYCLOAK_AUTH_URL = KEYCLOAK_BASE_URL + "//"
KEYCLOAK_TOKEN_AUTH_URL = "/".join(
    [
        KEYCLOAK_BASE_URL,
        "auth",
        "realms",
        KEYCLOAK_REALM_ID,
        "protocol",
        "openid-connect",
        "token",
    ]
)