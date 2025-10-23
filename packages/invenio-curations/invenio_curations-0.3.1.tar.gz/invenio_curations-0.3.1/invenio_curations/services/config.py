# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021-2025 Graz University of Technology.
#
# Invenio-Curations is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Curations service configuration."""

from typing import Final

from invenio_records_resources.services import RecordServiceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin, FromConfig
from invenio_requests.services.requests.config import RequestSearchOptions

from . import facets
from .permissions import CurationRDMRequestsPermissionPolicy


class CurationsSearchOptions(RequestSearchOptions):
    """Search options."""

    facets: Final = {
        "type": facets.type,
        "status": facets.status,
    }


class CurationsServiceConfig(RecordServiceConfig, ConfiguratorMixin):
    """Curations service configuration."""

    # will use requests service for most calls.
    service_id = "curations"

    # common configuration
    permission_policy_cls = FromConfig(
        "REQUESTS_PERMISSION_POLICY",
        default=CurationRDMRequestsPermissionPolicy,
    )
    # TODO: update search options?
    search = CurationsSearchOptions
