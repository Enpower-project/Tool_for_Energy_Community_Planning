from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware


import api.routers.values as values
import api.routers.baseline as baseline
import api.routers.context as context
import api.routers.catalogue as catalogue
import api.routers.alternatives as alternatives
from api.constants import API_VERSION, CORS_ORIGINS, EXTERNAL_ROOT_PATH

app = FastAPI(version=API_VERSION, root_path=EXTERNAL_ROOT_PATH)

# Config app middlewares (gzip and CORS)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoints routers
app.include_router(values.router)
app.include_router(baseline.router)
app.include_router(context.router)
app.include_router(catalogue.router)
app.include_router(alternatives.router)
