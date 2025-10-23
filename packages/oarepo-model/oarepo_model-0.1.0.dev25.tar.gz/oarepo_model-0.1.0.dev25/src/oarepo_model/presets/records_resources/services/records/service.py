#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.services.records.service import RecordService
from oarepo_runtime.services.config.components import ComponentsOrderingMixin

from oarepo_model.customizations import AddClass, AddMixins, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordServicePreset(Preset):
    """Preset for record service class."""

    provides = ("RecordService",)
    modifies = ("oarepo_model_arguments",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("RecordService", clazz=RecordService)
        yield AddMixins("RecordService", ComponentsOrderingMixin)
