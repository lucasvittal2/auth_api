import pytest
from fastapi.testclient import TestClient

from auth_api.app.api import auth_api
from auth_api.app.authentication import Authenticator
from auth_api.app.models import AuthConfig
from auth_api.databases.mongo import MongoHandler
from auth_api.utils.tools import read_yaml


@pytest.fixture
def test_client():
    """Fixture for creating a test client."""
    return TestClient(auth_api)


@pytest.fixture
def auth_config():
    """Fixture for loading authentication config."""
    AUTH_CONFIG = read_yaml("app_configs.yaml")["AUTH_CONFIG"]
    return AuthConfig(**AUTH_CONFIG)


@pytest.fixture
def mock_authenticator(auth_config):
    """Fixture for creating a mock Authenticator."""
    auth = Authenticator(auth_config)
    return auth


@pytest.fixture
def mock_mongo_handler():
    """Fixture for mocking MongoHandler."""
    mongo = MongoHandler("mongodb://localhost:27017/", "auth-api")
    return mongo


def test_signup_user_name_exists(test_client, mock_mongo_handler):
    """Test signup when the user name already exists."""
    mock_mongo_handler.get_document("app-test", {"user_name": "usertest5"})

    response = test_client.post(
        "/auth-api/v1/signup",
        json={
            "app_name": "app-test",
            "user_id": "99",
            "user_name": "usertest5",
            "password": "test123",
            "role": "user",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "FAILED",
        "message": "User with this name already exist ! Choose another user_name.",
    }


def test_signup_user_id_exists(test_client, mock_mongo_handler):
    """Test signup when the user name already exists."""

    response = test_client.post(
        "/auth-api/v1/signup",
        json={
            "app_name": "app-test",
            "user_id": "1",
            "user_name": "usertes99",
            "password": "test123",
            "role": "user",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "FAILED",
        "message": "User id already being used, use another user id!",
    }


def test_signup_success(test_client, mock_mongo_handler):
    """Test signup when the user name already exists."""

    USER_ID = 201
    response = test_client.post(
        "/auth-api/v1/signup",
        json={
            "app_name": "app-test",
            "user_id": USER_ID,
            "user_name": f"usertest{USER_ID}",
            "password": "test123",
            "role": "user",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "SUCCESS"}
    mock_mongo_handler.delete_document(
        "app-test", {"user_id": USER_ID, "user_name": f"usertest{USER_ID}"}
    )


def test_login_token_expired(test_client, mock_mongo_handler):
    """Test login when the token has expired."""

    doc_old_state = mock_mongo_handler.get_document(
        "app-test", filter_query={"user_name": "usertest10"}
    )
    response = test_client.post(
        "/auth-api/v1/login",
        json={
            "app_name": "app-test",
            "user_name": "usertest10",
            "password": "test123",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "AUTH_FAILED",
        "message": "Token has expired, please renew your credentials",
    }
    mock_mongo_handler.upsert("app-test", {"user_name": "usertest10"}, doc_old_state)


def test_login_wrong_credentials(test_client, mock_mongo_handler):
    """Test login when the token has expired."""

    response = test_client.post(
        "/auth-api/v1/login",
        json={
            "app_name": "app-test",
            "user_name": "usertest10",
            "password": "te123",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "USER_NOT_EXIST",
        "message": "User does not exist  or password is incorret! Try to signup.",
    }


def test_login_success(test_client, mock_mongo_handler):
    """Test login when the token has expired."""
    USER_ID = 150
    test_client.post(
        "/auth-api/v1/signup",
        json={
            "app_name": "app-test",
            "user_id": USER_ID,
            "user_name": f"usertest{USER_ID}",
            "password": "test123",
            "role": "user",
        },
    )

    response = test_client.post(
        "/auth-api/v1/login",
        json={
            "app_name": "app-test",
            "user_name": f"usertest{USER_ID}",
            "password": "test123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "AUTH_SUCCESS"}
    mock_mongo_handler.delete_document(
        "app-test", {"user_id": USER_ID, "user_name": f"usertest{USER_ID}"}
    )


def test_renew_with_wrong_credential(test_client):
    """Test successful credential renewal."""

    response = test_client.post(
        "/auth-api/v1/renew-credentials",
        json={
            "app_name": "app-test",
            "user_name": "usertest3",
            "old_password": "1234564",
            "new_password": "test123",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "ERROR",
        "message": "The password offered doesn't matched with current password or user does not exist.",
    }


def test_renew_same_new_and_old_password(test_client):
    """Test successful credential renewal."""

    response = test_client.post(
        "/auth-api/v1/renew-credentials",
        json={
            "app_name": "app-test",
            "user_name": "usertest3",
            "old_password": "123456",
            "new_password": "123456",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "ERROR",
        "message": "Not allowed using previous password",
    }


def test_renew_credentials_success(test_client, mock_mongo_handler):
    """Test successful credential renewal."""
    doc_old_state = mock_mongo_handler.get_document(
        "app-test", filter_query={"user_name": "usertest3"}
    )
    user_id = doc_old_state["user_id"]

    response = test_client.post(
        "/auth-api/v1/renew-credentials",
        json={
            "app_name": "app-test",
            "user_name": "usertest3",
            "old_password": "123456",
            "new_password": "test123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "SUCCESS",
        "message": f"User credentials for user id {user_id} renewed !",
    }
    mock_mongo_handler.upsert(
        "app-test", filter_query={"user_name": "usertest3"}, update_data=doc_old_state
    )
