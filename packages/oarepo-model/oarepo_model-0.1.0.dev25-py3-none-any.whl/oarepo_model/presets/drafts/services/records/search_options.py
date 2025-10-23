#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record search options class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.services.records.config import SearchDraftsOptions

from oarepo_model.customizations import AddClass, Customization
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

from oarepo_model.customizations import (
    AddMixins,
)
from oarepo_model.model import Dependency, InvenioModel, ModelMixin


class DraftSearchOptionsPreset(Preset):
    """Preset for record search options class."""

    provides = ("DraftSearchOptions",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        # yield AddDictionary("FacetGroups"FacetGroups, {}, exists_ok=True)
        class DraftSearchOptionsMixin(ModelMixin):
            facets = Dependency("RecordFacets")
            facet_groups = Dependency("FacetGroups")

        yield AddClass("DraftSearchOptions", clazz=SearchDraftsOptions)

        yield AddMixins("DraftSearchOptions", DraftSearchOptionsMixin)
