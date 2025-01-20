ARG PYTHON_IMAGE

# First stage: Build the wheel
FROM ${PYTHON_IMAGE} AS builder

ENV APP_NAME="AUTH-API"
WORKDIR ./auth_api

# Install build tools
RUN pip install --no-cache-dir build setuptools wheel

# Copy only the specific subdirectories from the source code
COPY src/auth_api/app ./auth_api/app
COPY src/auth_api/databases ./auth_api/databases
COPY src/auth_api/utils ./auth_api/utils
COPY src/auth_api/__init__.py ./auth_api/__init__.py


# Copy setup.py for building the wheel

COPY README.md ./
COPY src/setup.py ./
COPY .pkg/requirements.txt ./

# Build the distribution (sdist and wheel)
RUN python -m build

# Second stage: Final image
FROM ${PYTHON_IMAGE}


WORKDIR /auth_api

# Copy the built wheel from the builder stage
COPY --from=builder /auth_api/dist /auth_api/dist

# Install the built wheel
RUN pip install --no-cache-dir /auth_api/dist/*.whl

# Set the PYTHONPATH environment variable to point to the root module directory
ENV PYTHONPATH="/auth_api:${PYTHONPATH}"

# Verify installation (this ensures the module was installed correctly)
RUN python -c "import auth_api; print(auth_api.__file__)"

EXPOSE 8090
COPY app_configs.yaml ./
CMD ["uvicorn", "auth_api.app.api:auth_api", "--host", "0.0.0.0", "--port", "8090"]
