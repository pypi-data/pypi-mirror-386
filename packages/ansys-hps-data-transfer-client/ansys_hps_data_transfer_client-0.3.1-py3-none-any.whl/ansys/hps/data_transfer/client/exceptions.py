# Copyright (C) 2022 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Provides the base class for all client and server HPS-related errors."""

import httpx
from requests.exceptions import RequestException


class HPSError(RequestException):
    """Provides the base class for all HPS-related errors.

    This class derives from the :class:`requests.exceptions.RequestException`
    base class.

    Example:
        >>> from ansys.hps.client import HPSError
        >>> from ansys.hps.client.jms import Client
        >>> try:
        >>>     client = Client(url="https://127.0.0.1:8443/hps/",
                                username="repuser",
                                password="wrong_psw")
        >>> except HPSError as e:
        >>>     print(e)
        401 Client Error: invalid_grant for: POST https://127.0.0.1:8443/hps/auth...
        Invalid user credentials
    """

    def __init__(self, *args, **kwargs):
        """Initializes the HPSError class."""
        self.reason = kwargs.pop("reason", None)
        self.description = kwargs.pop("description", None)
        self.give_up = kwargs.pop("give_up", False)
        super().__init__(*args, **kwargs)


class APIError(HPSError):
    """Provides server-side related errors."""

    def __init__(self, *args, **kwargs):
        """Initializes the APIError class object."""
        super().__init__(*args, **kwargs)


class ClientError(HPSError):
    """Provides client-side related errors."""

    def __init__(self, *args, **kwargs):
        """Initializes the ClientError class object."""
        super().__init__(*args, **kwargs)


class BinaryError(HPSError):
    """Provides binary-related errors."""

    def __init__(self, *args, **kwargs):
        """Initializes the BinaryError class object."""
        super().__init__(*args, **kwargs)


class NotReadyError(ClientError):
    """Provides not ready-related errors."""

    def __init__(self, *args, **kwargs):
        """Initializes the NotReadyError class object."""
        super().__init__(*args, **kwargs)


class TimeoutError(ClientError):
    """Provides timeout-related errors."""

    def __init__(self, *args, **kwargs):
        """Initializes the TimeoutError class object."""
        super().__init__(*args, **kwargs)


def _raise_for_status(response: httpx.Response):
    r_content = {}
    try:
        r_content = response.json()
    except ValueError:
        pass

    reason = r_content.get("title", None)  # jms api
    if not reason:
        reason = r_content.get("error", None)  # auth api
    if not reason:
        reason = getattr(response, "reason", None)

    description = r_content.get("description", None)  # jms api
    if not description:
        description = r_content.get("error_description", None)  # auth api

    if response.status_code == 425:
        raise NotReadyError(
            response.status_code,
            reason=reason,
            description=description,
            response=response,
        )

    if 400 <= response.status_code < 500:
        error_msg = f"{response.status_code} Client Error: {reason} for: {response.request.method} {response.url}"
        if description:
            error_msg += f"\n{description}"

        give_up = response.status_code in [401, 403]
        raise ClientError(error_msg, reason=reason, description=description, response=response, give_up=give_up)
    elif 500 <= response.status_code < 600:
        error_msg = f"{response.status_code} Server Error: {reason} for: {response.request.method} {response.url}"
        if description:
            error_msg += f"\n{description}"
        raise APIError(error_msg, reason=reason, description=description, response=response)
    return response


def raise_for_status(response: httpx.Response):
    """Automatically check for HTTP errors.

    This method mimics the ``requests.Response.raise_for_status()`` method.
    """
    if response.status_code < 400 or response.status_code >= 600:
        return

    if getattr(response, "is_error", False):
        response.read()

    _raise_for_status(response)


async def async_raise_for_status(response: httpx.Response):
    """Automatically check for HTTP errors.

    This method mimics the ``requests.Response.raise_for_status()`` method.
    """
    if response.status_code < 400 or response.status_code >= 600:
        return

    if getattr(response, "is_error", False):
        await response.aread()

    _raise_for_status(response)
