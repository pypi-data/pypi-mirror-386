from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .environment import get_environment_variables  # Import environment loader

# Load environment variables
env = get_environment_variables()


def add_cors_middleware(app: FastAPI):
    origins = env.CORS_ORIGINS.split(",")

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["x-access-token"],
    )