from datetime import datetime

from pydantic import BaseModel


# Auth models
class AuthConfig(BaseModel):
    secret_key: str
    expire_delta: int
    algorithm: str
    encrypt_key: str
    salt: bytes


class RegisterPayload(BaseModel):
    app_name: str
    user_id: int
    user_name: str
    password: str
    role: str
    expire: str


class LoginPayload(BaseModel):
    user_name: str
    password: str
    expire: datetime


# API models
class RegisterRequest(BaseModel):
    app_name: str
    user_id: int
    user_name: str
    password: str
    role: str


class LoginRequest(BaseModel):
    app_name: str
    user_name: str
    password: str
