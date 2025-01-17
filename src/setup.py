import os
import re

import setuptools
from setuptools import find_packages

PROJECT_NAME = "auth_api"
AUTHOR_TEAM = "Lucas Vital"
AUTHOR_EMAIL = "lucasvittal@gmail.com"
DESCRIPTION = """
    API Created to authenticated applications in a plataform
"""


def get_version():
    with open("auth_api/__init__.py") as f:
        init_contents = f.read()
    version_match = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', init_contents, re.MULTILINE
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Version not found in __init__.py")


VERSION = get_version()


dependencies = [
    "google-cloud-secret-manager==2.20.0",
    "google-cloud-bigquery==3.26.0",
    "uvicorn==0.34.0",
    "fastapi==0.115.6",
    "pytz",
    "pymongo",
    "bcrypt",
    "PyJWT==2.10.1",
    "PyYAML==6.0.2",
]

setuptools.setup(
    name=PROJECT_NAME,
    version=VERSION,
    author=AUTHOR_TEAM,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    install_requires=dependencies,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
