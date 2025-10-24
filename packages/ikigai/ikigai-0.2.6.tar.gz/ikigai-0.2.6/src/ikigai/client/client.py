# SPDX-FileCopyrightText: 2024-present ikigailabs.io <harsh@ikigailabs.io>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
from dataclasses import InitVar
from typing import Any

from pydantic import AnyUrl, EmailStr, Field
from pydantic.dataclasses import dataclass
from requests import Response

from ikigai.client.api import ComponentAPI, SearchAPI
from ikigai.client.session import Session
from ikigai.utils.compatibility import HTTPMethod
from ikigai.utils.config import SSLConfig

logger = logging.getLogger("ikigai.client")


@dataclass
class Client:
    # Init only vars
    user_email: InitVar[EmailStr]
    api_key: InitVar[str]
    base_url: InitVar[AnyUrl]
    ssl: InitVar[SSLConfig]

    __session: Session = Field(init=False)
    __component_api: ComponentAPI = Field(init=False)
    __search_api: SearchAPI = Field(init=False)

    def __post_init__(
        self, user_email: EmailStr, api_key: str, base_url: AnyUrl, ssl: SSLConfig
    ) -> None:
        self.__session = Session(
            user_email=user_email, api_key=api_key, base_url=base_url, ssl=ssl
        )
        self.__component_api = ComponentAPI(session=self.__session)
        self.__search_api = SearchAPI(session=self.__session)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Response:
        return self.__session.request(method=HTTPMethod.GET, path=path, params=params)

    def post(self, path: str, json: dict[Any, Any] | None = None) -> Response:
        return self.__session.request(method=HTTPMethod.POST, path=path, json=json)

    # APIs

    @property
    def component(self) -> ComponentAPI:
        return self.__component_api

    @property
    def search(self) -> SearchAPI:
        return self.__search_api
