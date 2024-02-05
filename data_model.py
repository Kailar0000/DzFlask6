from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class User(BaseModel):
    id: int = Field(default=0, ge=0)
    name: str = Field(..., max_length=32)
    surname: str = Field(..., max_length=32)
    email: str = Field(..., max_length=128)
    password: str = Field(..., min_length=6, max_length=64)

    @field_validator("email")
    def check_email(cls, value):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email address")
        return value


class Product(BaseModel):
    id: int = Field(default=0, ge=0)
    name: str = Field(..., max_length=32)
    description: str = Field(..., max_length=128)
    cost: float = Field(..., gt=0)


class Order(BaseModel):
    id: int = Field(..., ge=0)
    user_id: int = Field(..., ge=0)
    product_id: int = Field(..., ge=0)
    date: datetime = Field(default_factory=datetime.now)
    status: bool = Field(default=False)