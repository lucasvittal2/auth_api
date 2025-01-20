# Auth API

## Table of Contents
- Pre-requisites
- Introduction
- How to run app ?
- Endpoints
  - POST /auth-api/v1/signup
  - POST /auth-api/v1/login
  - POST /auth-api/v1/renew-credentials
## Pre-requisites
 - Python 3.9.*
 - Docker installed
 - Linux/Ubuntu (to run app locally)
 - MongoDB running (Either locally or containerized)
## API Introduction

`auth_api` is a python  is python application focused on authentication users for multiple of applications. All te control performed by this application is made based on mongoDB Database which is schemed in following way:

- Each collection is focused in a single appication
- Each Document represent a user as long as the time of user's credentials is valid and also can be used to manage permissions of user inside the application which user was authenticated.

An example illustration how data is organized can be seen below for authentication control of an application called `app-test`:

Collection: app-test

```json
{
  "user_id": 110,
  "user_name": "usertest110",
  "password": "$2b$12$lRN6DqCd2k4E.RQMzB4YW.VvgadqrjqQwk3ZeydovrrTHUwCKkppi",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfbmFtZSI6InRlc3RfYXBwIiwidXNlcl9pZCI6MTEwLCJ1c2VyX25hbWUiOiJ1c2VydGVzdDExMCIsInBhc3N3b3JkIjoiJDJiJDEyJGxSTjZEcUNkMms0RS5SUU16QjRZVy5WdmdhZHFyanFRd2szWmV5ZG92cnJUSFV3Q0trcHBpIiwicm9sZSI6InVzZXIiLCJleHBpcmUiOiIyMDI1LTAyLTAxIDA5OjI1OjA5In0.FNmIHkJ7U0w75C8w04e3IMX_lDk2X0VlCaRJz_gP84w",
  "role": "user"
}
```

Because the security reason this auth_api also encrypted the user's password before storage it on  database.
The JWT token encode the encrypted password as well as the time user's credentials is valid.  They keys used to create JWT, to encrypt user password
as well as all other application can be setup on `app-config.yml` file

## How to run app ?

To run this applicatio you need make setup locally through command:
```commandline
make init
```
after that you'll be able to raise api locally:
```commandline
python src/auth_api/app/api.py
```
or building and raising container:
```commandline
    docker build -t auth_api:v1  --build-arg PYTHON_IMAGE="python:3.9" .
    docker run  -p 8080:8080 auth_api:v1
```
## API Endpoints

### POST /auth-api/v1/signup

**Purpose:**
Registers a new user for a specified application.

**Request Body:**
```json
{
    "app_name": "string",
    "user_id": "string",
    "user_name": "string",
    "password": "string",
    "role": "string"
}
```

**Responses:**

*200 OK:*
```json
{
    "status": "SUCCESS"
}
```
Indicates that the user was successfully registered.

*403 Forbidden:*

If the `user_id` is already in use:
```json
{
    "status": "FAILED",
    "message": "User id already being used, use another user id!"
}
```

If the `user_name` is already taken:
```json
{
    "status": "FAILED",
    "message": "User with this name already exist! Choose another user_name."
}
```

*500 Internal Server Error:*
```json
{
    "status": "FAILED",
    "message": "Sign up failed due to {error_message}"
}
```
Indicates an unexpected error occurred during the signup process.

**Example:**
```bash
curl -X POST "http://localhost:8000/auth-api/v1/signup" \
     -H "Content-Type: application/json" \
     -d '{
         "app_name": "app-test",
         "user_id": "99",
         "user_name": "usertest5",
         "password": "test123",
         "role": "user"
     }'
```

### POST /auth-api/v1/login

**Purpose:**
Authenticates a user and validates their token.

**Request Body:**
```json
{
    "app_name": "string",
    "user_name": "string",
    "password": "string"
}
```

**Responses:**

*200 OK:*
```json
{
    "status": "AUTH_SUCCESS"
}
```
Indicates successful authentication.

*403 Forbidden:*

If the user does not exist or the password is incorrect:
```json
{
    "status": "USER_NOT_EXIST",
    "message": "User does not exist or password is incorrect! Try to signup."
}
```

If the token has expired:
```json
{
    "status": "AUTH_FAILED",
    "message": "Token has expired, please renew your credentials"
}
```

If the token is invalid:
```json
{
    "status": "AUTH_FAILED",
    "message": "Token is invalid, contact your administrator"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/auth-api/v1/login" \
     -H "Content-Type: application/json" \
     -d '{
         "app_name": "app-test",
         "user_name": "usertest10",
         "password": "test123"
     }'
```

### POST /auth-api/v1/renew-credentials

**Purpose:**
Allows a user to renew their credentials by providing the old and new passwords.

**Request Body:**
```json
{
    "app_name": "string",
    "user_name": "string",
    "old_password": "string",
    "new_password": "string"
}
```

**Responses:**

*200 OK:*
```json
{
    "status": "SUCCESS",
    "message": "User credentials for user id {user_id} renewed!"
}
```
Indicates that the user's credentials were successfully renewed.

*403 Forbidden:*

If the old password doesn't match the current password or the user does not exist:
```json
{
    "status": "ERROR",
    "message": "The password offered doesn't match the current password or user does not exist."
}
```

If the new password is the same as the old password:
```json
{
    "status": "ERROR",
    "message": "Not allowed using previous password"
}
```

*500 Internal Server Error:*
```json
{
    "status": "ERROR",
    "message": "Failed to renew user credentials, please contact your administrator."
}
```
Indicates an unexpected error occurred during the credential renewal process.

**Example:**
```bash
curl -X POST "http://localhost:8000/auth-api/v1/renew-credentials" \
     -H "Content-Type: application/json" \
     -d '{
         "app_name": "app-test",
         "user_name": "usertest3",
         "old_password": "123456",
         "new_password": "test123"
     }'
```
