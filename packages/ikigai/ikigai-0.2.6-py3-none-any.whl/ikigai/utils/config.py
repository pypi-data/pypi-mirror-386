# SPDX-FileCopyrightText: 2025-present ikigailabs.io <harsh@ikigailabs.io>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Annotated, Union

from typing_extensions import TypeAlias

PemFilepath: TypeAlias = Annotated[
    str, "Path to a PEM file containing SSL certificates"
]
CertKeyPair: TypeAlias = Annotated[
    tuple[str, str], "Tuple containing certificate and key"
]

# Define a type alias for SSL configuration
SSLConfig: TypeAlias = Union[bool, PemFilepath, CertKeyPair]
