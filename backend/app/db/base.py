from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

#Creates engine object to interact with PostgreSQL
engine = create_engine(settings.database_url, pool_pre_ping=True)

#Creates a database session object for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Creates a base class for all models/class
Base = declarative_base()

#function for fastAPI route
#new db session to request and waits to closes when finished for route
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()