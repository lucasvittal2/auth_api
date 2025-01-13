from datetime import datetime

from pydantic import BaseModel


class AuthConfig(BaseModel):
    secret_key: str
    expire_delta: int
    algorithm: str
    encrypt_key: str


class RegisterPayload(BaseModel):
    user_id: int
    username: str
    password: str
    role: str
    expire: str


class LoginPayload(BaseModel):
    username: str
    password: str
    expire: datetime
