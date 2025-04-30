from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base
from sqlalchemy import Boolean


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    current_package = Column(String, nullable=True)
    license_key = Column(String, nullable=True)
