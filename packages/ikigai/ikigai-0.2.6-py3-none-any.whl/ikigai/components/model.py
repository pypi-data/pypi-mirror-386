# SPDX-FileCopyrightText: 2024-present ikigailabs.io <harsh@ikigailabs.io>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from ikigai.client.client import Client
from ikigai.components.specs import SubModelSpec
from ikigai.typing.protocol import Directory, DirectoryType, NamedDirectoryDict
from ikigai.utils.compatibility import Self, deprecated
from ikigai.utils.named_mapping import NamedMapping

logger = logging.getLogger("ikigai.components")


class ModelBrowser:
    __app_id: str
    __client: Client

    def __init__(self, app_id: str, client: Client) -> None:
        self.__app_id = app_id
        self.__client = client

    @deprecated("Prefer directly loading by name:\n\tapp.models['model_name']")
    def __call__(self) -> NamedMapping[Model]:
        models = {
            model["model_id"]: Model.from_dict(data=model, client=self.__client)
            for model in self.__client.component.get_models_for_app(
                app_id=self.__app_id
            )
        }

        return NamedMapping(models)

    def __getitem__(self, name: str) -> Model:
        model_dict = self.__client.component.get_model_by_name(
            app_id=self.__app_id, name=name
        )

        return Model.from_dict(data=model_dict, client=self.__client)

    def search(self, query: str) -> NamedMapping[Model]:
        matching_models = {
            model["model_id"]: Model.from_dict(data=model, client=self.__client)
            for model in self.__client.search.search_models_for_project(
                app_id=self.__app_id, query=query
            )
        }

        return NamedMapping(matching_models)


class ModelBuilder:
    _app_id: str
    _name: str
    _directory: Directory | None
    _model_type: SubModelSpec | None
    _description: str
    __client: Client

    def __init__(self, client: Client, app_id: str) -> None:
        self.__client = client
        self._app_id = app_id
        self._name = ""
        self._directory = None
        self._model_type = None
        self._description = ""

    def new(self, name: str) -> Self:
        self._name = name
        return self

    def directory(self, directory: Directory) -> Self:
        self._directory = directory
        return self

    def model_type(self, model_type: SubModelSpec) -> Self:
        self._model_type = model_type
        return self

    def description(self, description: str) -> Self:
        self._description = description
        return self

    def build(self) -> Model:
        if self._model_type is None:
            error_msg = "Model type must be specified"
            raise ValueError(error_msg)

        model_id = self.__client.component.create_model(
            app_id=self._app_id,
            name=self._name,
            directory=self._directory,
            model_type=self._model_type,
            description=self._description,
        )
        # Populate the model object
        model_dict = self.__client.component.get_model(
            app_id=self._app_id, model_id=model_id
        )

        return Model.from_dict(data=model_dict, client=self.__client)


class Model(BaseModel):
    app_id: str = Field(validation_alias=AliasChoices("app_id", "project_id"))
    model_id: str
    name: str
    model_type: str
    sub_model_type: str
    description: str
    created_at: str
    modified_at: str
    __client: Client

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], client: Client) -> Self:
        logger.debug("Creating a %s from %s", cls.__name__, data)
        self = cls.model_validate(data)
        self.__client = client
        return self

    def delete(self) -> None:
        self.__client.component.delete_model(app_id=self.app_id, model_id=self.model_id)
        return None

    def rename(self, name: str) -> Self:
        self.__client.component.edit_model(
            app_id=self.app_id, model_id=self.model_id, name=name
        )
        self.name = name
        return self

    def move(self, directory: Directory) -> Self:
        self.__client.component.edit_model(
            app_id=self.app_id, model_id=self.model_id, directory=directory
        )
        return self

    def update_description(self, description: str) -> Self:
        self.__client.component.edit_model(
            app_id=self.app_id, model_id=self.model_id, description=description
        )
        self.description = description
        return self

    def versions(self) -> NamedMapping[ModelVersion]:
        version_dicts = self.__client.component.get_model_versions(
            app_id=self.app_id, model_id=self.model_id
        )
        versions = {
            version.version_id: version
            for version in (
                ModelVersion.from_dict(
                    app_id=self.app_id, data=version_dict, client=self.__client
                )
                for version_dict in version_dicts
            )
        }

        return NamedMapping(versions)

    def describe(self) -> Mapping[str, Any]:
        return self.__client.component.get_model(
            app_id=self.app_id, model_id=self.model_id
        )


class ModelVersion(BaseModel):
    app_id: str = Field(validation_alias=AliasChoices("app_id", "project_id"))
    model_id: str
    version_id: str
    version: str
    hyperparameters: dict[str, Any]
    metrics: dict[str, Any]
    created_at: str
    modified_at: str
    __client: Client

    @property
    def name(self) -> str:
        # Implement the named protocol
        return self.version

    @classmethod
    def from_dict(cls, app_id: str, data: Mapping[str, Any], client: Client) -> Self:
        logger.debug("Creating a %s from %s", cls.__name__, data)
        self = cls.model_validate({"app_id": app_id, **data})
        self.__client = client
        return self

    def describe(self) -> Mapping[str, Any]:
        return self.__client.component.get_model_version(
            app_id=self.app_id, version_id=self.version_id
        )


class ModelDirectoryBuilder:
    _app_id: str
    _name: str
    _parent: Directory | None
    __client: Client

    def __init__(self, client: Client, app_id: str) -> None:
        self.__client = client
        self._app_id = app_id
        self._name = ""
        self._parent = None

    def new(self, name: str) -> ModelDirectoryBuilder:
        self._name = name
        return self

    def parent(self, parent: Directory) -> ModelDirectoryBuilder:
        self._parent = parent
        return self

    def build(self) -> ModelDirectory:
        directory_id = self.__client.component.create_model_directory(
            app_id=self._app_id, name=self._name, parent=self._parent
        )
        directory_dict = self.__client.component.get_model_directory(
            app_id=self._app_id, directory_id=directory_id
        )

        return ModelDirectory.from_dict(data=directory_dict, client=self.__client)


class ModelDirectory(BaseModel):
    app_id: str = Field(validation_alias=AliasChoices("app_id", "project_id"))
    directory_id: str
    name: str
    __client: Client

    @property
    def type(self) -> DirectoryType:
        return DirectoryType.MODEL

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], client: Client) -> Self:
        logger.debug("Creating a %s from %s", cls.__name__, data)
        self = cls.model_validate(data)
        self.__client = client
        return self

    def to_dict(self) -> NamedDirectoryDict:
        return {"directory_id": self.directory_id, "type": self.type, "name": self.name}

    def directories(self) -> NamedMapping[Self]:
        directory_dicts = self.__client.component.get_model_directories_for_app(
            app_id=self.app_id, parent=self
        )
        directories = {
            directory.directory_id: directory
            for directory in (
                self.from_dict(data=directory_dict, client=self.__client)
                for directory_dict in directory_dicts
            )
        }

        return NamedMapping(directories)

    def models(self) -> NamedMapping[Model]:
        model_dicts = self.__client.component.get_models_for_app(
            app_id=self.app_id, directory_id=self.directory_id
        )

        models = {
            model.model_id: model
            for model in (
                Model.from_dict(data=model_dict, client=self.__client)
                for model_dict in model_dicts
            )
        }

        return NamedMapping(models)
