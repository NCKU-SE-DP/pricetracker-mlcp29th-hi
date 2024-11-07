from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import configuration


engine = create_engine(configuration.database_url, echo=True)


def get_database():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


def get_database_with_auto_persist_changes_disabled():
    return Session(autocommit=False, autoflush=False, bind=engine)