from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if " " in value:
            raise ValueError("Password must not contain spaces.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()_+=\[\]{}:;\"'<>,.?/\\|~`-]", value):
            raise ValueError("Password must contain at least one special character.")
        return value




class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    current_package: str | None = None
    license_key: str | None = None

    class Config:
        from_attributes = True

