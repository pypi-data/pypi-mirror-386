#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""OARepo model customizations and builders package.

This package provides a way of building an Invenio model with user customizations.
It allows you to add mixins, classes to components, routes and other customizations
to the model while ensuring that the model remains consistent, functional and upgradable.
"""

from __future__ import annotations

from .datatypes.registry import from_json, from_yaml

__version__ = "0.1.0dev25"
__all__ = ["__version__", "from_json", "from_yaml"]
