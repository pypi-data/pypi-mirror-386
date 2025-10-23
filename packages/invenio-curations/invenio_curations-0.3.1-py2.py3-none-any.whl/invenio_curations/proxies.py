# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 Graz University of Technology.
#
# Invenio-Curations is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Proxies for accessing the currently instantiated curations extension."""

from typing import cast

from flask import current_app
from werkzeug.local import LocalProxy


# the funny thing is the ignore was necessary after started using ruff, which
# should not interfere with mypy
def unproxy[T](obj: LocalProxy[T]) -> T:  # type: ignore[type-var]
    """Cast to the proxy bound object."""
    return cast(T, obj)


current_curations = LocalProxy(lambda: current_app.extensions["invenio-curations"])
"""Proxy for the instantiated curations extension."""

current_curations_service = LocalProxy(lambda: current_curations.curations_service)
"""Proxy to the instantiated curations service."""
