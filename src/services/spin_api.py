import base64
import hashlib
import logging
import os
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SpinBot:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.base_url = "https://spinco.marianatek.com"
        self.client_id = "sbLziNCoF5HcOhkSV6zRL8O7betwd3mDDIQbWZa3"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.token_data: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

    def _generate_pkce(self):
        """Generates PKCE verifier and challenge for the OAuth flow."""
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("utf-8")).digest()
        ).decode("utf-8").rstrip("=")
        return verifier, challenge

    def authenticate(self) -> bool:
        self.last_error = None
        self.token_data = None
        verifier, challenge = self._generate_pkce()

        login_page_url = f"{self.base_url}/auth/login/"
        auth_params = {
            "next": (
                f"/o/authorize/?client_id={self.client_id}&scope=read:account"
                f"&response_type=code&code_challenge={challenge}&code_challenge_method=S256"
            )
        }

        logger.debug("Fetching login page")
        res = self.session.get(login_page_url, params=auth_params, timeout=30)
        if not res.ok:
            self.last_error = f"Login page request failed (HTTP {res.status_code})"
            logger.warning(self.last_error)
            return False

        soup = BeautifulSoup(res.text, "html.parser")
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if not csrf_input or not csrf_input.get("value"):
            self.last_error = "Could not find CSRF token on login page"
            logger.warning(self.last_error)
            return False
        csrf_token = csrf_input["value"]

        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "username": self.email,
            "password": self.password,
            "next": auth_params["next"],
        }

        logger.debug("Submitting credentials")
        res = self.session.post(
            login_page_url,
            data=payload,
            headers={"Referer": res.url},
            allow_redirects=True,
            timeout=30,
        )

        match = re.search(r"code=([^&]+)", res.url or "")
        if not match:
            self.last_error = "No authorization code in redirect (check credentials or site changes)"
            logger.warning("Login redirect missing code; url=%s", res.url)
            return False
        code = match.group(1)

        token_url = f"{self.base_url}/o/token/"
        token_data = {
            "client_id": self.client_id,
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": "https://spinco.marianaiframes.com/iframe/callback/",
        }

        logger.debug("Exchanging code for token")
        token_res = self.session.post(token_url, data=token_data, timeout=30)
        if token_res.status_code != 200:
            self.last_error = f"Token exchange failed (HTTP {token_res.status_code})"
            logger.warning(self.last_error)
            return False

        try:
            data = token_res.json()
        except ValueError:
            self.last_error = "Token response was not valid JSON"
            logger.warning(self.last_error)
            return False

        if "access_token" not in data:
            self.last_error = data.get("error_description") or data.get("error") or "No access_token in response"
            logger.warning("Token response missing access_token")
            return False

        self.token_data = data
        logger.info("Authentication successful")
        return True

    def get_account_data(self):
        api_url = f"{self.base_url}/api/v2/voice/account/"
        res = self.session.get(api_url, timeout=30)
        res.raise_for_status()
        return res.json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    MY_EMAIL = "your_email@example.com"
    MY_PASSWORD = "your_password_here"

    bot = SpinBot(MY_EMAIL, MY_PASSWORD)
    if bot.authenticate():
        data = bot.get_account_data()
        print(f"\nWelcome, {data.get('first_name')}!")
        print(f"Home Studio: {data.get('home_location', {}).get('name')}")
