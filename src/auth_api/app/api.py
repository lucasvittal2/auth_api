import logging
from datetime import datetime, timedelta
from http.client import responses
from typing import Dict, Tuple

import pytz
import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth_api.app.authentication import Authenticator
from auth_api.app.models import *
from auth_api.databases.mongo import MongoHandler
from auth_api.utils.file_handling import read_yaml

# Instance vars and objects globally used
APP_CONFIGS = read_yaml("app_configs.yaml")
APP_NAME = APP_CONFIGS["APP_NAME"]
TIME_ZONE = pytz.timezone(APP_CONFIGS["TIME_ZONE"])
mongo = MongoHandler(**APP_CONFIGS["AUTH_DB"])
auth_config = AuthConfig(**APP_CONFIGS["AUTH_CONFIG"])
authenticator = Authenticator(auth_config)

# Logging setup

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)


logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - [{APP_NAME}] - %(levelname)s:  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)


# set app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define API Endpoints


def delta_parse(delta_str: str) -> Dict[str, int]:
    days, hours, minutes, seconds = map(int, delta_str.split(":"))
    return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}


@app.post("/auth-api/v1/signup")
def singup(body_request: RegisterRequest) -> JSONResponse:
    try:
        mongo.create_collection_if_not_exist(body_request.app_name)
        hashed_password = authenticator.hash_password(body_request.password)
        delta_params = delta_parse(APP_CONFIGS["TIME_DELTA"])
        expire = datetime.now(tz=TIME_ZONE) + timedelta(**delta_params)
        payload = RegisterPayload(
            **body_request.model_dump(), expire=expire.strftime("%Y-%m-%d %H:%M:%S")
        )
        token = authenticator.create_jwt_token(payload)
        document = {
            "user_id": body_request.user_id,
            "user_name": body_request.user_name,
            "password": hashed_password,
            "token": token,
            "role": body_request.role,
        }
        user_name_exists = mongo.get_document(
            body_request.app_name, filter_query={"user_name": body_request.user_name}
        )
        userid_used = mongo.get_document(
            body_request.app_name, filter_query={"user_id": body_request.user_id}
        )

        if userid_used:
            response = JSONResponse(
                content={
                    "status": "FAILED",
                    "message": "User id already being used, use another user id!",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

        elif not user_name_exists:
            mongo.create(body_request.app_name, document)
            response = JSONResponse(
                content={"status": "SUCCESS"}, status_code=status.HTTP_200_OK
            )
            logging.info("new user recorded successfully !")

        else:
            response = JSONResponse(
                content={
                    "status": "FAILED",
                    "message": "User with this name already exist ! Choose another user_name.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

    except Exception as err:
        response = JSONResponse(
            content={"status": "FAILED", "message": f" sign up failed due to {err}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


@app.post("/auth-api/v1/login")
def login(body_request: LoginRequest) -> JSONResponse:
    try:
        hashed_password = authenticator.hash_password(body_request.password)
        now = datetime.now(tz=TIME_ZONE)
        document = mongo.get_document(
            body_request.app_name,
            {"user_name": body_request.user_name, "password": hashed_password},
        )

        if document is None:
            response = JSONResponse(
                content={
                    "status": "USER_NOT_EXIST",
                    "message": "User does not exist ! Try to signup.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )
            return response

        token = document["token"]
        status_auth = authenticator.validate_jwt_token(token, now, TIME_ZONE)

        if status_auth == "VALID_TOKEN":
            response = JSONResponse(
                content={"status": "AUTH_SUCCESS"}, status_code=status.HTTP_200_OK
            )
        elif status_auth == "TOKEN_EXPIRED":
            response = JSONResponse(
                content={
                    "status": "AUTH_FAILED",
                    "message": "Token has expired, please renew your credentials",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )
        elif status_auth == "INVALID_TOKEN":
            response = JSONResponse(
                content={
                    "status": "AUTH_FAILED",
                    "message": "Token is invalid, enter in contact with your administrator",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )
    except Exception as err:
        logging.error(f"Login has failed: \n\n {err}")

    return response


@app.post("/auth-api/v1/renew-credentials")
def renew_credentials(body_request: RenewCredentialsRequest) -> JSONResponse:
    try:
        hashed_old_password = authenticator.hash_password(body_request.old_password)
        hashed_new_password = authenticator.hash_password(body_request.new_password)
        filter = {"user_name": body_request.user_name, "password": hashed_old_password}
        document = mongo.get_document(
            body_request.app_name,
            {"user_name": body_request.user_name, "password": hashed_old_password},
        )

        if document is None:
            response = JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "The password offered doesn't matched with current password or user does not exist.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

        elif hashed_new_password == document["password"]:
            response = JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "Not allowed using previous password",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )
        else:
            delta_params = delta_parse(APP_CONFIGS["TIME_DELTA"])
            expire = datetime.now(tz=TIME_ZONE) + timedelta(**delta_params)
            payload = RegisterPayload(
                app_name=body_request.app_name,
                user_id=document["user_id"],
                user_name=body_request.user_name,
                password=hashed_new_password,
                role=document["role"],
                expire=expire.strftime("%Y-%m-%d %H:%M:%S"),
            )
            token = authenticator.create_jwt_token(payload)
            new_doc = {**payload.model_dump(), "token": token}
            mongo.upsert(body_request.app_name, filter, new_doc)
            user_id = document["user_id"]
            response = JSONResponse(
                content={
                    "status": "SUCCESS",
                    "message": f"User credentials for user id {user_id} renewed !",
                }
            )

    except Exception as err:
        logging.error(f"Failed to renew user credentials: \n\n{err}")
        response = JSONResponse(
            content={
                "status": "ERROR",
                "message": "Failed to renew user credentials, please contact your administrator.",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


if __name__ == "__main__":
    api_configs = APP_CONFIGS["API_CONFIGS"]
    uvicorn.run(
        app,
        log_level=api_configs["LOG_LEVEL"],
        port=api_configs["PORT"],
        log_config=APP_CONFIGS["LOGGING_CONFIG"],
        host=api_configs["HOST"],
    )
