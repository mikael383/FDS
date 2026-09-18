import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchor database consistently to the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "fayda_dispatch.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.replace(os.sep, '/')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
