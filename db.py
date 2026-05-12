import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)

# Import models AFTER Base
import models


def create_tables():
    print(Base.metadata.tables)

    Base.metadata.create_all(bind=engine)

    print("Tables created successfully.")


if __name__ == "__main__":
    create_tables()
