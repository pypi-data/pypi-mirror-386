import json
import logging
import os
from abc import ABC
from io import BytesIO
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union

import requests

from msal_bearer import Authenticator, get_user_name

_eq_tenant_id = "3aa4a235-b6e2-48d5-9195-7fcf05b459b0"
_eq_domain = "equinor.com"

logger = logging.getLogger(__name__)


def get_object_from_json(text: str):
    if isinstance(text, list):
        obj = [json.loads(x, object_hook=lambda d: SimpleNamespace(**d)) for x in text]
    else:
        obj = json.loads(text, object_hook=lambda d: SimpleNamespace(**d))
    return obj


class Connector(ABC):
    def __init__(self) -> None:
        self._use_dev = False
        self._url_prod = ""
        self._url_dev = ""
        self.authenticator = None

    def set_url_prod(self, url: str) -> None:
        """Setter for property _url_prod.

        Args:
            url (str): URL to set.
        """
        self._url_prod = url

    def set_url_dev(self, url: str) -> None:
        """Setter for property _url_dev.

        Args:
            url (str): URL to set.
        """
        self._url_dev = url

    def set_use_dev(self, use_dev: bool):
        """Setter for global property _use_dev.
        If _use_dev is True, the API URL will be set to the development URL,
        otherwise it will be set to the production URL.

        Args:
            use_dev (bool): Value to set _use_dev to.

        Raises:
            TypeError: In case input use_dev is not a boolean.
        """
        if not isinstance(use_dev, bool):
            raise TypeError("Input use_dev shall be boolean.")

        self._use_dev = use_dev

    def get_url(self) -> str:
        """Getter for URL. Will return the dev URL if _use_dev is True, otherwise will return the production URL.
        Returns:
            str: API URL
        """
        if self._use_dev:
            return self._url_dev
        else:
            return self._url_prod

    def set_Authenticator(self, authenticator: Authenticator) -> None:
        """Setter for property authenticator.

        Args:
            authenticator (Authenticator): Authenticator to set.
        """
        if not isinstance(authenticator, Authenticator):
            raise TypeError("Input authenticator shall be of type Authenticator.")

        self.authenticator = authenticator


class APIConnector(Connector):
    def __init__(
        self,
        tenant_id: Optional[str] = _eq_tenant_id,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[Union[List[str], str]] = None,
        user_name: Optional[str] = None,
        user_assertion: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._raise_for_status = True

        if user_name is None:
            user_name = f"{get_user_name()}"
            if "@" not in user_name:
                user_name = f"{user_name}@{_eq_domain}"

        if client_id or scope:
            a = Authenticator(
                tenant_id=tenant_id,
                client_id=client_id,
                scopes=scope if scope else None,
                client_secret=client_secret if client_secret else None,
                user_name=user_name,
                user_assertion=user_assertion,
            )
            self.set_Authenticator(a)

    def get_token(self) -> str:
        """Get access token from authenticator.

        Returns:
            str: Access token.
        """
        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        return self.authenticator.get_token()

    def set_raise_for_status(self, raise_for_status: bool):
        """Setter for  property _raise_for_status.
        If _raise_for_status is True, the requests will raise an exception for HTTP errors,
        otherwise it will not.

        Args:
            raise_for_status (bool): Value to set _raise_for_status to.

        Raises:
            TypeError: In case input raise_for_status is not a boolean.
        """

        if not isinstance(raise_for_status, bool):
            raise TypeError("Input raise_for_status shall be boolean.")

        self._raise_for_status = raise_for_status

    def get_json(
        self, url: str, params: Optional[dict] = None
    ) -> Union[dict, requests.Response]:
        """Get JSON from API endpoint.

        Args:
            url (str): _description_
            params (Optional[dict], optional): _description_. Defaults to None.

        Returns:
            Union[dict, requests.Response]: _description_
        """

        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        if url.startswith("/"):
            url = self.get_url() + url

        header = {"Authorization": f"Bearer {self.authenticator.get_token()}"}
        response = requests.get(url, headers=header, params=params)
        if self._raise_for_status:
            response.raise_for_status()

        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.warning(
                    f"Warning: {str(url)} returned successfully, but not with a valid json response"
                )
        else:
            logger.warning(
                f"Warning: {str(url)} returned status code {response.status_code}"
            )

        return response

    def get_file(self, url: str, file_name: str, stream=True) -> str:
        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        if url.startswith("/"):
            url = self.get_url() + url

        header = {"Authorization": f"Bearer {self.authenticator.get_token()}"}
        response = requests.get(url, headers=header, stream=stream)
        if self._raise_for_status:
            response.raise_for_status()

        if not (response.status_code == 200):
            logger.warning(
                f"Warning: {str(url)} returned status code {response.status_code}"
            )

        if file_name is not None and len(file_name) > 0:
            save_path = os.path.join(os.getcwd(), file_name)
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File downloaded successfully and saved to {save_path}")
            return save_path
        else:
            return response.text
        # except requests.exceptions.RequestException as e:
        #     print(f"Error downloading schema: {e}")
        # except PermissionError as e:
        #     print(f"Permission error: {e}")
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")

    def post(self, url: str, params: Optional[dict] = None, data: Optional[Any] = None):
        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        if url.startswith("/"):
            url = self.get_url() + url

        header = {"Authorization": f"Bearer {self.authenticator.get_token()}"}
        response = requests.post(url, headers=header, data=data, params=params)
        if self._raise_for_status:
            response.raise_for_status()

        if not (response.status_code == 200):
            logger.warning(
                f"Warning: {str(url)} returned status code {response.status_code}"
            )

        return response

    def post_json(self, url: str, upload: Dict[str, List[Dict[str, str]]]):
        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        if url.startswith("/"):
            url = self.get_url() + url

        header = {"Authorization": f"Bearer {self.authenticator.get_token()}"}
        response = requests.post(url, headers=header, json=upload)
        if self._raise_for_status:
            response.raise_for_status()

        if not (response.status_code == 200):
            logger.warning(
                f"Warning: {str(url)} returned status code {response.status_code}"
            )

        return response

    def post_file(self, url: str, upload: Dict[str, List[Dict[str, str]]]):
        if not self.authenticator:
            raise ValueError("Authenticator is not set")

        if url.startswith("/"):
            url = self.get_url() + url

        header = {"Authorization": f"Bearer {self.authenticator.get_token()}"}
        json_file = BytesIO(json.dumps(upload).encode("utf-8"))
        response = requests.post(
            url, headers=header, files={"file": ("upload_data.json", json_file)}
        )
        if self._raise_for_status:
            response.raise_for_status()

        if not (response.status_code == 200):
            logger.warning(
                f"Warning: {str(url)} returned status code {response.status_code}"
            )

        return response
