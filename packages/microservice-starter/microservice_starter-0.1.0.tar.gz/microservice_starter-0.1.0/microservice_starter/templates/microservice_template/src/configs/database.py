from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .environment import get_environment_variables

# Runtime Environment Configuration
env = get_environment_variables()

# Generate Database URL
SQL_DATABASE_URL = (
    f"{env.DATABASE_DIALECT}://{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}"
    f"@{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}/{env.DATABASE_NAME}"
)

# Create Database Engine
Engine = create_engine(
    SQL_DATABASE_URL,
    echo=env.DEBUG_MODE,
    future=True,
    pool_size=10,  # Increase base pool size
    max_overflow=20,  # Allow temporary overflow connections
    pool_timeout=60,  # Wait longer before timeout
    pool_recycle=1800,  # Recycle connections after 30 min
    pool_pre_ping=True,  # Validate connection before using
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=Engine, expire_on_commit=False
)


def get_db_connection():
    db = scoped_session(SessionLocal)
    try:
        yield db
    finally:
        db.close()
