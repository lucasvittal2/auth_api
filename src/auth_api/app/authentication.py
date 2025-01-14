import logging
from datetime import datetime, timedelta
from typing import Union

import bcrypt
import jwt
import pytz

from auth_api.app.models import AuthConfig, LoginPayload, RegisterPayload


class Authenticator:
    def __init__(self, configs: AuthConfig):
        self.secret_key = configs.secret_key
        self.algorithm = configs.algorithm
        self.expire_delta = configs.expire_delta  # minutes
        self.encrypt_key = configs.encrypt_key

    def create_jwt_token(self, payload: RegisterPayload) -> str:

        try:
            jwt_payload = payload.model_dump()
            print(jwt_payload)
            token = jwt.encode(jwt_payload, self.secret_key, algorithm=self.algorithm)
            logging.info("Created token succefully.")
            return token
        except Exception as err:
            logging.error(f"Error when try to create token: {err}")
            raise err

    def validate_jwt_token(self, token_to_validate) -> Union[str, LoginPayload]:
        try:
            decoded_payload = jwt.decode(
                token_to_validate, self.secret_key, algorithms=[self.algorithm]
            )
            logging.info("Token Validated with success.")
        except jwt.ExpiredSignatureError:
            logging.error("Token has expired. Please renew your credentials.")
            decoded_payload = "TOKEN_EXPIRED"
        except jwt.InvalidTokenError:
            logging.error("Invalid token. Access denied.")
            decoded_payload = "INVALID_TOKEN"

        return decoded_payload

    def hash_password(self, password: str) -> str:
        password_with_key = f"{password}{self.encrypt_key}"
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_with_key.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:

        try:

            password_with_key = f"{password}{self.encrypt_key}"
            return bcrypt.checkpw(
                password_with_key.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as err:
            logging.error(f"Error verifying password: {err}")
            raise Exception


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv("../../../.env")
    brazil_timezone = pytz.timezone("America/Sao_Paulo")
    expire = datetime.now(tz=brazil_timezone) + timedelta(hours=1)

    payload = RegisterPayload(
        user_id=777,
        username="tom",
        password=os.getenv("TEST_PASSWORD"),
        role="mouse_catcher",
        expire=expire.strftime("%Y-%m-%d %H:%M:%S"),  # Token will expire in 1 hour
    )

    configs = AuthConfig(
        secret_key=os.getenv("SECRET_KEY"),
        encrypt_key=os.getenv("ENCRIPTION_KEY"),
        algorithm="HS256",
        expire_delta=1,
    )
    authenticator = Authenticator(configs)
    token = authenticator.create_jwt_token(payload)
    # Validate and decode the token
    decoded_payload = authenticator.validate_jwt_token(token)
    if decoded_payload:
        # If the decoding is successful, you can trust the token!
        print("Decoded Payload:", decoded_payload)

    hashed_psw = authenticator.hash_password(payload.password)
    print(hashed_psw)
    print(authenticator.verify_password("123", hashed_psw))
