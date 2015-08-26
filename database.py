"""
Creates the necessary variables for database interaction
Database settings are defined in settings.yml
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils import read_settings

db = read_settings()["database"]

engine = create_engine(db, convert_unicode=True)
Base = declarative_base(engine)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base.query = db_session.query_property()
