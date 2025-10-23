#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Extension preset for media file handling functionality.

This module provides the ExtMediaFilesPreset that configures
the Flask extension for handling published record media files in Invenio applications.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.config import build_config

from oarepo_model.customizations import (
    AddMixins,
    AddToList,
    Customization,
)
from oarepo_model.model import InvenioModel, ModelMixin
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.ext_files import (
    RecordWithFilesExtensionProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from invenio_records_resources.resources.files import FileResource
    from invenio_records_resources.services.files import FileService

    from oarepo_model.builder import InvenioModelBuilder


class ExtMediaFilesPreset(Preset):
    """Preset for extension class."""

    modifies = ("Ext",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class ExtMediaFilesMixin(ModelMixin, RecordWithFilesExtensionProtocol):
            """Mixin for extension class."""

            app: Flask

            @cached_property
            def media_files_service(self) -> FileService:
                return self.get_model_dependency("MediaFileService")(
                    **self.media_files_service_params,
                )

            @property
            def media_files_service_params(self) -> dict[str, Any]:
                """Parameters for the file service."""
                return {
                    "config": build_config(
                        self.get_model_dependency("MediaFileServiceConfig"),
                        self.app,
                    ),
                }

            @cached_property
            def media_files_resource(self) -> FileResource:
                return self.get_model_dependency("MediaFileResource")(
                    **self.media_files_resource_params,
                )

            @property
            def media_files_resource_params(self) -> dict[str, Any]:
                """Parameters for the file resource."""
                return {
                    "service": self.media_files_service,
                    "config": build_config(
                        self.get_model_dependency("MediaFileResourceConfig"),
                        self.app,
                    ),
                }

            @property
            def model_arguments(self) -> dict[str, Any]:
                """Model arguments for the extension."""
                return {
                    **super().model_arguments,
                    "media_file_service": self.media_files_service,
                }

        yield AddMixins("Ext", ExtMediaFilesMixin)

        yield AddToList(
            "services_registry_list",
            (
                lambda ext: ext.media_files_service,
                lambda ext: ext.media_files_service.config.service_id,
            ),
        )
