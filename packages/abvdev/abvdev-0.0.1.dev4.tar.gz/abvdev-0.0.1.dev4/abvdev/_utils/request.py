"""@private"""

import json
import logging
from base64 import b64encode
from typing import Any, List, Union

import httpx

from abvdev._utils.serializer import EventSerializer


class ABVClient:
    _api_key: str
    _base_url: str
    _version: str
    _timeout: int
    _session: httpx.Client

    def __init__(
        self,
        api_key: str,
        base_url: str,
        version: str,
        timeout: int,
        session: httpx.Client,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._version = version
        self._timeout = timeout
        self._session = session

    def generate_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "x_abv_sdk_name": "python",
            "x_abv_sdk_version": self._version,
        }

    def batch_post(self, **kwargs: Any) -> httpx.Response:
        """Post the `kwargs` to the batch API endpoint for events"""
        log = logging.getLogger("abv")
        log.debug("uploading data: %s", kwargs)

        res = self.post(**kwargs)
        return self._process_response(
            res, success_message="data uploaded successfully", return_json=False
        )

    def post(self, **kwargs: Any) -> httpx.Response:
        """Post the `kwargs` to the API"""
        log = logging.getLogger("abv")
        url = self._remove_trailing_slash(self._base_url) + "/api/public/ingestion"
        data = json.dumps(kwargs, cls=EventSerializer)
        log.debug("making request: %s to %s", data, url)
        headers = self.generate_headers()
        res = self._session.post(
            url, content=data, headers=headers, timeout=self._timeout
        )

        if res.status_code == 200:
            log.debug("data uploaded successfully")

        return res

    def _remove_trailing_slash(self, url: str) -> str:
        """Removes the trailing slash from a URL"""
        if url.endswith("/"):
            return url[:-1]
        return url

    def _process_response(
        self, res: httpx.Response, success_message: str, *, return_json: bool = True
    ) -> Union[httpx.Response, Any]:
        log = logging.getLogger("abv")
        log.debug("received response: %s", res.text)
        if res.status_code in (200, 201):
            log.debug(success_message)
            if return_json:
                try:
                    return res.json()
                except json.JSONDecodeError:
                    raise APIError(res.status_code, "Invalid JSON response received")
            else:
                return res
        elif res.status_code == 207:
            try:
                payload = res.json()
                errors = payload.get("errors", [])
                if errors:
                    raise APIErrors(
                        [
                            APIError(
                                error.get("status"),
                                error.get("message", "No message provided"),
                                error.get("error", "No error details provided"),
                            )
                            for error in errors
                        ]
                    )
                else:
                    return res.json() if return_json else res
            except json.JSONDecodeError:
                raise APIError(res.status_code, "Invalid JSON response received")

        try:
            payload = res.json()
            raise APIError(res.status_code, payload)
        except (KeyError, ValueError):
            raise APIError(res.status_code, res.text)


class APIError(Exception):
    def __init__(self, status: Union[int, str], message: str, details: Any = None):
        self.message = message
        self.status = status
        self.details = details

    def __str__(self) -> str:
        msg = "{0} ({1}): {2}"
        return msg.format(self.message, self.status, self.details)


class APIErrors(Exception):
    def __init__(self, errors: List[APIError]):
        self.errors = errors

    def __str__(self) -> str:
        errors = ", ".join(str(error) for error in self.errors)

        return f"[ABV] {errors}"
