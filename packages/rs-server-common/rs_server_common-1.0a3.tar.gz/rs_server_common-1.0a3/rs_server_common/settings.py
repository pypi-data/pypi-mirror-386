# Copyright 2024 CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Store diverse objects and values used throughout the application."""

import os
from os import environ as env

from httpx import AsyncClient
from starlette.requests import Request

#########################
# Environment variables #
#########################


def env_bool(var: str, default: bool) -> bool:
    """
    Return True if an environemnt variable is set to 1, true or yes (case insensitive).
    Return False if set to 0, false or no (case insensitive).
    Return the default value if not set or set to a different value.
    """
    val = os.getenv(var, str(default)).lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    return default


# True if the 'RSPY_LOCAL_MODE' environemnt variable is set to 1, true or yes (case insensitive).
# By default: if not set or set to a different value, return False.
LOCAL_MODE: bool = env_bool("RSPY_LOCAL_MODE", default=False)

# Cluster mode is the opposite of local mode
CLUSTER_MODE: bool = not LOCAL_MODE

# STAC browser URL(s), as seen from the user browser, separated by commas e.g. http://url1,http://url2
CORS_ORIGINS: list[str] = [url.strip() for url in os.environ.get("CORS_ORIGINS", "").split(";") if url]


def request_from_stacbrowser(request: Request) -> bool:
    """Return if the HTTP request comes from the STAC browser."""
    return bool((origin := request.headers.get("origin")) and (origin.rstrip("/") in CORS_ORIGINS))


def docs_params(prefix: str = "") -> dict[str, str]:
    """
    Return the docs parameters for the FastAPI application.

    Args:
        prefix (str, optional): Prefix to prepend to default values, when RSPY_DOCS_URL is not set. Defaults to "".

    Returns:
        dict[str, str]: dict with FastAPI docs_url and openapi_url keys.
    """
    # For cluster deployment: override the swagger /docs URL from an environment variable.
    # Also set the openapi.json URL under the same path.
    if "RSPY_DOCS_URL" in env:
        docs_url = env["RSPY_DOCS_URL"].strip("/")
        return {"docs_url": f"/{docs_url}", "openapi_url": f"/{docs_url}/openapi.json"}
    return {"docs_url": prefix + "/api.html", "openapi_url": prefix + "/api"}  # Default values from stac-fastapi


###################
# Other variables #
###################

# Service name for logging and OpenTelemetry
SERVICE_NAME: str | None = None


###############
# HTTP client #
###############

__http_client: AsyncClient | None = None


def http_client():
    """Get HTTP client"""
    return __http_client


def set_http_client(value):
    """Set HTTP client"""
    global __http_client  # pylint: disable=global-statement
    __http_client = value


async def del_http_client():
    """Close and delete HTTP client."""
    global __http_client  # pylint: disable=global-statement
    if __http_client:
        await __http_client.aclose()
    __http_client = None
