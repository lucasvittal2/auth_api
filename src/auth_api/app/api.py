import logging
from datetime import datetime, timedelta

import pytz
import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth_api.app.authentication import Authenticator
from auth_api.app.models import *
from auth_api.databases.mongo import MongoHandler
from auth_api.utils.file_handling import read_yaml

# Instance objects globally used
app_configs = read_yaml("app_configs.yaml")
app_name = app_configs["APP_NAME"]
time_zone = pytz.timezone(app_configs["TIME_ZONE"])
mongo = MongoHandler(**app_configs["AUTH_DB"])
auth_config = AuthConfig(**app_configs["AUTH_CONFIG"])
authenticator = Authenticator(auth_config)

# Logging setup

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)


logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - [{app_name}] - %(levelname)s:  %(message)s",
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


@app.post("/auth-api/v1/signup")
def singup(body_request: RegisterRequest) -> JSONResponse:
    try:
        mongo.create_collection_if_not_exist(body_request.app_name)
        hashed_password = authenticator.hash_password(body_request.password)
        expire = datetime.now(tz=time_zone) + timedelta(hours=1)
        payload = RegisterPayload(
            **body_request.model_dump(), expire=expire.strftime("%Y-%m-%d %H:%M:%S")
        )
        token = authenticator.create_jwt_token(payload)
        document = {
            "user_id": body_request.user_id,
            "user_name": body_request.username,
            "password": hashed_password,
            "token": token,
            "role": body_request.role,
        }
        username_exists = mongo.get_document(
            body_request.app_name, filter_query={"user_name": body_request.username}
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

        elif not username_exists:
            mongo.create(body_request.app_name, document)
            response = JSONResponse(
                content={"status": "SUCCESS"}, status_code=status.HTTP_200_OK
            )
            logging.info("new user recorded successfully !")

        else:
            response = JSONResponse(
                content={
                    "status": "FAILED",
                    "message": "User with this name already exist ! Choose another username.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )

    except Exception as err:
        response = JSONResponse(
            content={"status": "FAILED", "message": f" sign up failed due to {err}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


if __name__ == "__main__":
    api_configs = app_configs["API_CONFIGS"]
    uvicorn.run(
        app,
        log_level=api_configs["LOG_LEVEL"],
        port=api_configs["PORT"],
        log_config=app_configs["LOGGING_CONFIG"],
        host=api_configs["HOST"],
    )
