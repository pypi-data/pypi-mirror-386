# SPDX-FileCopyrightText: 2024-present ikigailabs.io <harsh@ikigailabs.io>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from ikigai import components
from ikigai.client import Client
from ikigai.typing.protocol import Directory, DirectoryType, NamedDirectoryDict
from ikigai.utils.compatibility import Self, deprecated
from ikigai.utils.component_browser import ComponentBrowser
from ikigai.utils.named_mapping import NamedMapping


class AppBrowser:
    __client: Client

    def __init__(self, client: Client) -> None:
        self.__client = client

    @deprecated("Prefer directly loading by name:\n\tikigai.apps['app_name']")
    def __call__(self) -> NamedMapping[App]:
        apps = {
            app["project_id"]: components.App.from_dict(data=app, client=self.__client)
            for app in self.__client.component.get_apps_for_user()
        }

        return NamedMapping(apps)

    def __getitem__(self, name: str) -> App:
        app_dict = self.__client.component.get_app_by_name(name)
        return components.App.from_dict(data=app_dict, client=self.__client)

    def search(self, query: str) -> NamedMapping[App]:
        matching_apps = {
            app["project_id"]: components.App.from_dict(data=app, client=self.__client)
            for app in self.__client.search.search_projects_for_user(query=query)
        }

        return NamedMapping(matching_apps)


class AppBuilder:
    _name: str
    _description: str
    _directory: Directory | None
    _icon: str
    _images: list[str]
    __client: Client

    def __init__(self, client: Client) -> None:
        self.__client = client
        self._name = ""
        self._description = ""
        self._directory = None
        self._icon = ""
        self._images = []

    def new(self, name: str) -> Self:
        self._name = name
        return self

    def description(self, description: str) -> Self:
        self._description = description
        return self

    def directory(self, directory: Directory) -> Self:
        self._directory = directory
        return self

    def build(self) -> App:
        app_id = self.__client.component.create_app(
            name=self._name,
            description=self._description,
            directory=self._directory,
        )
        app_dict = self.__client.component.get_app(app_id=app_id)
        return App.from_dict(data=app_dict, client=self.__client)


class App(BaseModel):
    app_id: str = Field(validation_alias="project_id")
    name: str
    owner: EmailStr
    description: str
    created_at: datetime
    modified_at: datetime
    last_used_at: datetime
    __client: Client

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], client: Client) -> Self:
        self = cls.model_validate(data)
        self.__client = client
        return self

    """
    Operations on App
    """

    def to_dict(self) -> dict:
        return {
            "app_id": self.app_id,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "last_used_at": self.last_used_at,
        }

    def delete(self) -> None:
        self.__client.component.delete_app(app_id=self.app_id)
        return None

    def rename(self, name: str) -> Self:
        _ = self.__client.component.edit_app(app_id=self.app_id, name=name)
        # TODO: handle error case, currently it is a raise NotImplemented from Session
        self.name = name
        return self

    def move(self, directory: Directory) -> Self:
        _ = self.__client.component.edit_app(app_id=self.app_id, directory=directory)
        return self

    def update_description(self, description: str) -> Self:
        _ = self.__client.component.edit_app(
            app_id=self.app_id, description=description
        )
        # TODO: handle error case, currently it is a raise NotImplemented from Session
        self.description = description
        return self

    def describe(self) -> dict[str, Any]:
        components = self.__client.component.get_components_for_app(app_id=self.app_id)

        # Combine components information with app info
        return {
            "app": self.to_dict(),
            "components": components,
        }

    """
    Access Components in the App
    """

    @property
    def datasets(self) -> ComponentBrowser[components.Dataset]:
        return components.DatasetBrowser(app_id=self.app_id, client=self.__client)

    @property
    def dataset(self) -> components.DatasetBuilder:
        return components.DatasetBuilder(client=self.__client, app_id=self.app_id)

    def dataset_directories(self) -> NamedMapping[components.DatasetDirectory]:
        directory_dicts = self.__client.component.get_dataset_directories_for_app(
            app_id=self.app_id
        )
        directories = {
            directory.directory_id: directory
            for directory in (
                components.DatasetDirectory.from_dict(
                    data=directory_dict, client=self.__client
                )
                for directory_dict in directory_dicts
            )
        }

        return NamedMapping(directories)

    @property
    def dataset_directory(self) -> components.DatasetDirectoryBuilder:
        return components.DatasetDirectoryBuilder(
            client=self.__client, app_id=self.app_id
        )

    @property
    def flows(self) -> ComponentBrowser[components.Flow]:
        return components.FlowBrowser(app_id=self.app_id, client=self.__client)

    @property
    def flow(self) -> components.FlowBuilder:
        return components.FlowBuilder(client=self.__client, app_id=self.app_id)

    def flow_directories(self) -> NamedMapping[components.FlowDirectory]:
        directory_dicts = self.__client.component.get_flow_directories_for_app(
            app_id=self.app_id
        )
        directories = {
            directory.directory_id: directory
            for directory in (
                components.FlowDirectory.from_dict(
                    data=directory_dict, client=self.__client
                )
                for directory_dict in directory_dicts
            )
        }

        return NamedMapping(directories)

    @property
    def flow_directory(self) -> components.FlowDirectoryBuilder:
        return components.FlowDirectoryBuilder(client=self.__client, app_id=self.app_id)

    @property
    def models(self) -> ComponentBrowser[components.Model]:
        return components.ModelBrowser(app_id=self.app_id, client=self.__client)

    @property
    def model(self) -> components.ModelBuilder:
        return components.ModelBuilder(client=self.__client, app_id=self.app_id)

    def model_directories(self) -> NamedMapping[components.ModelDirectory]:
        directory_dicts = self.__client.component.get_model_directories_for_app(
            app_id=self.app_id
        )
        directories = {
            directory.directory_id: directory
            for directory in (
                components.ModelDirectory.from_dict(
                    data=directory_dict, client=self.__client
                )
                for directory_dict in directory_dicts
            )
        }

        return NamedMapping(directories)

    @property
    def model_directory(self) -> components.ModelDirectoryBuilder:
        return components.ModelDirectoryBuilder(
            client=self.__client, app_id=self.app_id
        )


class AppDirectory(BaseModel):
    directory_id: str
    name: str
    created_at: datetime
    modified_at: datetime
    __client: Client

    @property
    def type(self) -> DirectoryType:
        return DirectoryType.APP

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], client: Client) -> Self:
        self = cls.model_validate(data)
        self.__client = client
        return self

    def to_dict(self) -> NamedDirectoryDict:
        return {"directory_id": self.directory_id, "type": self.type, "name": self.name}

    def directories(self) -> NamedMapping[Self]:
        directory_dicts = self.__client.component.get_app_directories_for_user(
            directory_id=self.directory_id,
        )
        directories = {
            directory.directory_id: directory
            for directory in (
                self.from_dict(data=directory_dict, client=self.__client)
                for directory_dict in directory_dicts
            )
        }

        return NamedMapping(directories)

    def apps(self) -> NamedMapping[App]:
        app_dicts = self.__client.component.get_apps_for_user(
            directory_id=self.directory_id
        )

        apps = {
            app.app_id: app
            for app in (
                App.from_dict(data=app_dict, client=self.__client)
                for app_dict in app_dicts
            )
        }

        return NamedMapping(apps)
