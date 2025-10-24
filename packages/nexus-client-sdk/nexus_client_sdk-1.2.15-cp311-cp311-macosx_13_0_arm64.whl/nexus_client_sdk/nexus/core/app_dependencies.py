"""
 Dependency injections.
"""
#  Copyright (c) 2023-2026. ECCO Data & AI and other project contributors.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import re
from pydoc import locate
from typing import final, Any, Callable, Self

from adapta.storage.blob.base import StorageClient
from adapta.storage.query_enabled_store import QueryEnabledStore
from injector import Module, singleton, provider

from nexus_client_sdk.nexus.abstractions.algorithm_cache import InputCache
from nexus_client_sdk.nexus.abstractions.logger_factory import (
    BootstrapLoggerFactory,
)
from nexus_client_sdk.nexus.abstractions.socket_provider import (
    ExternalSocketProvider,
)
from nexus_client_sdk.nexus.configurations.algorithm_configuration import (
    NexusConfiguration,
)
from nexus_client_sdk.nexus.exceptions.startup_error import (
    FatalStartupConfigurationError,
)
from nexus_client_sdk.nexus.input.input_processor import InputProcessor
from nexus_client_sdk.nexus.input.input_reader import InputReader
from nexus_client_sdk.nexus.telemetry.recorder import TelemetryRecorder
from nexus_client_sdk.nexus.core.serializers import (
    TelemetrySerializer,
    ResultSerializer,
)


@final
class BootstrapLoggerFactoryModule(Module):
    """
    Logger factory module.
    """

    @singleton
    @provider
    def provide(self) -> BootstrapLoggerFactory:
        """
        DI factory method.
        """
        return BootstrapLoggerFactory()


@final
class QueryEnabledStoreModule(Module):
    """
    QES module.
    """

    @singleton
    @provider
    def provide(self) -> QueryEnabledStore:
        """
        DI factory method.
        """
        return QueryEnabledStore.from_string(os.getenv("NEXUS__QES_CONNECTION_STRING"), lazy_init=False)


@final
class StorageClientModule(Module):
    """
    Storage client module.
    """

    @singleton
    @provider
    def provide(self) -> StorageClient:
        """
        DI factory method.
        """
        storage_client_class: type[StorageClient] = locate(
            os.getenv(
                "NEXUS__STORAGE_CLIENT_CLASS",
            )
        )
        if not storage_client_class:
            raise FatalStartupConfigurationError("NEXUS__STORAGE_CLIENT_CLASS")
        if "NEXUS__ALGORITHM_OUTPUT_PATH" not in os.environ:
            raise FatalStartupConfigurationError("NEXUS__ALGORITHM_OUTPUT_PATH")

        try:
            return storage_client_class.for_storage_path(path=os.getenv("NEXUS__ALGORITHM_OUTPUT_PATH"))
        except Exception as e:
            raise FatalStartupConfigurationError(
                "StorageClient cannot be created, configuration missing or invalid. Review the underlying exception."
            ) from e


@final
class ExternalSocketsModule(Module):
    """
    Storage client module.
    """

    @singleton
    @provider
    def provide(self) -> ExternalSocketProvider:
        """
        Dependency provider.
        """
        if "NEXUS__ALGORITHM_INPUT_EXTERNAL_DATA_SOCKETS" not in os.environ:
            raise FatalStartupConfigurationError("NEXUS__ALGORITHM_INPUT_EXTERNAL_DATA_SOCKETS")

        return ExternalSocketProvider.from_serialized(os.getenv("NEXUS__ALGORITHM_INPUT_EXTERNAL_DATA_SOCKETS"))


@final
class ResultSerializerModule(Module):
    """
    Serialization format module for results.
    """

    @singleton
    @provider
    def provide(self) -> ResultSerializer:
        """
        DI factory method.
        """
        serializer = ResultSerializer()
        for serialization_format in locate_classes(re.compile(r"NEXUS__RESULT_SERIALIZATION_FORMAT_(.+)_CLASS")):
            serializer = serializer.with_format(serialization_format)

        return serializer


@final
class TelemetrySerializerModule(Module):
    """
    Serialization format module for telemetry.
    """

    @singleton
    @provider
    def provide(self) -> TelemetrySerializer:
        """
        DI factory method.
        """
        serializer = TelemetrySerializer()
        for serialization_format in locate_classes(re.compile(r"NEXUS__TELEMETRY_SERIALIZATION_FORMAT_(.+)_CLASS")):
            serializer = serializer.with_format(serialization_format)

        return serializer


@final
class CacheModule(Module):
    """
    Storage client module.
    """

    @singleton
    @provider
    def provide(self) -> InputCache:
        """
        Dependency provider.
        """
        return InputCache()


@final
class Compressor:
    """
    Compression and decompression support for remote algorithm payloads.
    """

    def __init__(self, compress_import_path: str, decompress_import_path: str):
        self._compress_import_path = compress_import_path
        self._decompress_import_path = decompress_import_path
        self._compress_function: Callable[
            [
                bytes,
            ],
            bytes,
        ] = locate(self._compress_import_path)
        self._decompress_function: Callable[
            [
                bytes,
            ],
            bytes,
        ] = locate(self._decompress_import_path)

        if not self._compress_function:
            raise FatalStartupConfigurationError(
                f"Compression function '{self._compress_import_path}' from NEXUS__REMOTE_ALGORITHM_COMPRESSION_IMPORT_PATH could not be located."
            )
        if not self._decompress_function:
            raise FatalStartupConfigurationError(
                f"Decompression function '{self._decompress_import_path}' from NEXUS__REMOTE_ALGORITHM_DECOMPRESSION_IMPORT_PATH could not be located."
            )

    @classmethod
    def create(cls, compress_import_path: str, decompress_import_path: str) -> Self:
        """
        Factory method to create a compressor instance.
        """
        try:
            return cls(compress_import_path, decompress_import_path)
        except Exception as ex:
            raise FatalStartupConfigurationError("compress or decompress import path could not be resolved.") from ex

    def compress(self, data: bytes) -> bytes:
        """
        Compresses the given data using the configured compression function.
        """
        return self._compress_function(data)

    def decompress(self, data: bytes) -> bytes:
        """
        Decompresses the given data using the configured decompression function.
        """
        return self._decompress_function(data)

    @property
    def compressor_import_path(self) -> str:
        """
        Returns the import path of the compression function.
        """
        return self._compress_import_path

    @property
    def decompressor_import_path(self) -> str:
        """
        Returns the import path of the decompression function.
        """
        return self._decompress_import_path


@final
class CompressorModule(Module):
    """
    Compression configuration module.
    """

    @singleton
    @provider
    def provide(self) -> Compressor:
        """
        Returns a compressor if configured, else None.
        """
        compress_path = os.getenv("NEXUS__REMOTE_ALGORITHM_COMPRESSION_IMPORT_PATH")
        decompress_path = os.getenv("NEXUS__REMOTE_ALGORITHM_DECOMPRESSION_IMPORT_PATH")

        if compress_path is None and decompress_path is None:
            return None

        if compress_path is None and decompress_path is not None:
            raise FatalStartupConfigurationError(
                "NEXUS__REMOTE_ALGORITHM_COMPRESSION_IMPORT_PATH must be set if NEXUS__REMOTE_ALGORITHM_DECOMPRESSION_IMPORT_PATH is set."
            )

        if compress_path is not None and decompress_path is None:
            raise FatalStartupConfigurationError(
                "NEXUS__REMOTE_ALGORITHM_DECOMPRESSION_IMPORT_PATH must be set if NEXUS__REMOTE_ALGORITHM_COMPRESSION_IMPORT_PATH is set."
            )

        return Compressor.create(compress_path, decompress_path)


@final
class ServiceConfigurator:
    """
    Runtime DI support.
    """

    def __init__(self):
        self._injection_binds = [
            BootstrapLoggerFactoryModule(),
            QueryEnabledStoreModule(),
            StorageClientModule(),
            ExternalSocketsModule(),
            TelemetrySerializerModule(),
            ResultSerializerModule(),
            CacheModule(),
            CompressorModule(),
            type(f"{TelemetryRecorder.__name__}Module", (Module,), {})(),
        ]
        self._runtime_injection_binds = []

    @property
    def injection_binds(self) -> list:
        """
        Currently configured injection bindings
        """
        return self._injection_binds

    @property
    def runtime_injection_binds(self) -> list:
        """
        Currently configured injection bindings that are added at runtime
        """
        return self._runtime_injection_binds

    def with_module(self, module: type[Module]) -> "ServiceConfigurator":
        """
        Adds a (custom) module into the DI container.
        """
        self._injection_binds.append(module())
        return self

    def with_input_reader(self, reader: type[InputReader]) -> "ServiceConfigurator":
        """
        Adds the input reader implementation to the DI.
        """
        self._injection_binds.append(type(f"{reader.__name__}Module", (Module,), {})())
        return self

    def with_input_processor(self, input_processor: type[InputProcessor]) -> "ServiceConfigurator":
        """
        Adds the input processor implementation
        """
        self._injection_binds.append(type(f"{input_processor.__name__}Module", (Module,), {})())
        return self

    def with_configuration(self, config: NexusConfiguration) -> "ServiceConfigurator":
        """
        Adds the specified payload instance to the DI container.
        """
        self._injection_binds.append(lambda binder: binder.bind(config.__class__, to=config, scope=singleton))
        return self


def locate_classes(pattern: re.Pattern) -> list[type[Any]]:
    """
    Locates all classes matching the pattern in the environment. Throws a start-up error if any class is not found.
    """
    classes = {
        (var_name, class_path): locate(class_path)
        for var_name, class_path in os.environ.items()
        if pattern.match(var_name)
    }

    non_located_classes = [name_and_path for name_and_path, class_ in classes.items() if class_ is None]
    if non_located_classes:
        raise FatalStartupConfigurationError(f"Failed to locate classes: {non_located_classes}")

    return list(classes.values())
