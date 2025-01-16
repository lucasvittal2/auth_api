import logging
from datetime import datetime, timedelta
from typing import Union

import bcrypt
import jwt
import pytz
from pytz import timezone

from auth_api.app.models import AuthConfig, LoginPayload, RegisterPayload


class Authenticator:
    def __init__(self, configs: AuthConfig):
        self.secret_key = configs.secret_key
        self.algorithm = configs.algorithm
        self.expire_delta = configs.expire_delta  # minutes
        self.encrypt_key = configs.encrypt_key
        self.salt = configs.salt

    def create_jwt_token(self, payload: RegisterPayload) -> str:

        try:
            logging.info("Creating JWT Token...")
            jwt_payload = payload.model_dump()
            jwt_payload["password"] = self.hash_password(jwt_payload["password"])
            token = jwt.encode(jwt_payload, self.secret_key, algorithm=self.algorithm)
            logging.info("Created token succefully.")
            return token
        except Exception as err:
            logging.error(f"Error when try to create token: {err}")
            raise err

    def validate_jwt_token(
        self, token_to_validate, now: datetime, tz: timezone
    ) -> Union[str, LoginPayload]:
        try:
            logging.info("Validating token...")
            decoded = jwt.decode(
                token_to_validate, self.secret_key, algorithms=[self.algorithm]
            )
            expire = datetime.strptime(decoded["expire"], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=tz
            )
            now_norm = now.replace(tzinfo=tz)

            if now_norm > expire:
                status = "TOKEN_EXPIRED"
                logging.error("Token is expired, please renew your credentials")
            else:
                status = "VALID_TOKEN"
                logging.info("Token Validated with success.")

        except jwt.InvalidTokenError:
            logging.error("Invalid token. Access denied.")
            status = "INVALID_TOKEN"

        return status

    def hash_password(self, password: str) -> str:
        logging.info("Hashing password...")
        password_with_key = f"{password}{self.encrypt_key}"

        hashed_password = bcrypt.hashpw(password_with_key.encode("utf-8"), self.salt)
        logging.info("Hashin password completed !")
        return hashed_password.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:

        try:
            logging.info("Verifying password...")
            password_with_key = f"{password}{self.encrypt_key}"
            return bcrypt.checkpw(
                password_with_key.encode("utf-8"), hashed_password.encode("utf-8")
            )
            logging.info("Verified password successfully")
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
