"""Module for custom authentication"""

import json
import os
import sys
from datetime import datetime, timezone
import requests
from dateutil.parser import parse
from requests.auth import AuthBase
import logging

class RefreshToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, access_key, secret_key):
        self.bearer_token = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.VALIDATE_ACCESS_KEY_URL = (
            f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai/v1/accounting/validate_access_key"
        )

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain a bearer token using the provided access key and secret key."""
        payload_dict = {
            "accessKey": self.access_key,
            "secretKey": self.secret_key,
        }
        payload = json.dumps(payload_dict)
        headers = {"Content-Type": "text/plain"}
        response = None
        try:
            response = requests.request(
                "GET",
                self.VALIDATE_ACCESS_KEY_URL,
                headers=headers,
                data=payload,
                timeout=120,
            )
        except Exception as e:
            logging.error("Error while making request to the auth server in RefreshToken")
            logging.error(e)
            return

        if not response or response.status_code != 200:
            logging.error("Error response from the auth server in RefreshToken")
            logging.error(getattr(response, "text", "No response text"))
            return

        try:
            res_dict = response.json()
        except Exception as e:
            logging.error("Invalid JSON in RefreshToken response")
            logging.error(e)
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("refreshToken"):
            logging.debug(f"res_dict: {res_dict}")
            self.bearer_token = "Bearer " + res_dict["data"]["refreshToken"]
        else:
            logging.error("The provided credentials are incorrect!! in RefreshToken")


class AuthToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(
        self,
        access_key,
        secret_key,
        refresh_token,
    ):
        self.bearer_token = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.refresh_token = refresh_token
        self.expiry_time = datetime.now(timezone.utc)
        self.REFRESH_TOKEN_URL = (
            f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai/v1/accounting/refresh"
        )

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain an authentication bearer token using the provided refresh token."""
        headers = {"Content-Type": "application/json"}
        response = None
        try:
            response = requests.request(
                "POST",
                self.REFRESH_TOKEN_URL,
                headers=headers,
                auth=self.refresh_token,
                timeout=120,
            )
        except Exception as e:
            logging.error("Error while making request to the auth server in AuthToken")
            logging.error(e)
            return

        if not response or response.status_code != 200:
            logging.error("Error response from the auth server in AuthToken")
            logging.error(getattr(response, "text", "No response text"))
            return

        try:
            res_dict = response.json()
        except Exception as e:
            logging.error("Invalid JSON in AuthToken response")
            logging.error(e)
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("token"):
            self.bearer_token = "Bearer " + res_dict["data"]["token"]
            self.expiry_time = parse(res_dict["data"]["expiresAt"])
        else:
            logging.error("The provided credentials are incorrect!! in AuthToken")
