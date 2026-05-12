from sqlalchemy import Column, Integer, String, Text, ForeignKey

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(255))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_text = Column(Text)
    result = Column(Text)
