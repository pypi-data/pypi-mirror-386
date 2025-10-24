from fastapi import FastAPI
from src.configs.environment import get_environment_variables
from src.configs.middleware import add_cors_middleware
from src.routers.v1.check_router import CheckHealthRouter

# Application Environment Configuration
env = get_environment_variables()

if env.DEBUG_MODE == "False":
    print("Running in Production Mode")
    app = FastAPI(
        title=env.APP_NAME,
        version=env.API_VERSION,
        debug=True,
        docs_url=None,
        redoc_url=None,
    )
else:
    print("Running in Development Mode")
    app = FastAPI(
        title=env.APP_NAME,
        version=env.API_VERSION,
        debug=True,
        docs_url="/docs",
        redoc_url="/redoc",
    )

# Add Middleware
add_cors_middleware(app)

app.include_router(CheckHealthRouter)

