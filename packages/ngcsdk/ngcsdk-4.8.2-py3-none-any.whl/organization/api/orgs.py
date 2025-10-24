#
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

from typing import Optional

from ngcbase.api.pagination import pagination_helper
from ngcbase.constants import API_VERSION, PAGE_SIZE, SCOPED_KEY_PREFIX
from ngcbase.printer.nvPrettyPrint import NVPrettyPrint
from ngcbase.util.utils import extra_args
from organization.data.uis.Organization import Organization
from organization.data.uis.OrgListResponse import OrgListResponse


class OrgAPI:  # noqa: D101
    SERVICE_KEY_ERROR_MESSAGE = (
        "This command requires a personal API key.\n"
        "Service keys cannot be used for this operation. Please login again using a personal key:\n"
        "  ngc config set --api-key <your-personal-key>"
    )

    def __init__(self, api_client):
        self.connection = api_client.connection
        self.client = api_client
        self.printer = NVPrettyPrint(self.client.config)

    def get_org_list(self):
        """List all the organizations user can access."""
        query = f"{API_VERSION}/orgs?page-size={PAGE_SIZE}"
        return self._helper_get_orgs(query)

    @extra_args
    def list(self):
        """List all the organizations the user can access."""
        # Only validate scoped keys (nvapi-) for SERVICE_KEY blocking
        if self.client.config.app_key and self.client.config.app_key.startswith(SCOPED_KEY_PREFIX):
            key_details = self.client.authentication.get_sak_key_details(self.client.config.app_key)
            if getattr(key_details, "type", None) == "SERVICE_KEY":
                self.printer.print_error(self.SERVICE_KEY_ERROR_MESSAGE)
                return []

        # Legacy keys and personal scoped keys proceed normally
        self.client.config.validate_configuration(csv_allowed=True)
        return self.get_org_list()

    def get_org_detail(self, org_name: str):
        """List details of an organization."""
        response = self.connection.make_api_request(
            "GET",
            f"{API_VERSION}/orgs/{org_name}",
            auth_org=org_name,
            operation_name="get org details",
        )
        return Organization(response.get("organizations", {}))

    @extra_args
    def info(self, org: Optional[str] = None):
        """Display detailed information about the specified organization.

        If no organization is provided, uses the configured default. Requires a personal API key.
        """
        # Only validate scoped keys (nvapi-) for SERVICE_KEY blocking
        if self.client.config.app_key and self.client.config.app_key.startswith(SCOPED_KEY_PREFIX):
            key_details = self.client.authentication.get_sak_key_details(self.client.config.app_key)
            if getattr(key_details, "type", None) == "SERVICE_KEY":
                self.printer.print_error(self.SERVICE_KEY_ERROR_MESSAGE)
                return Organization({})

        # Legacy keys and personal scoped keys proceed normally
        self.client.config.validate_configuration()
        org_name = org or self.client.config.org_name
        return self.get_org_detail(org_name=org_name)

    def _helper_get_orgs(self, query):
        """Helper command to get list of all the orgs using pagination."""  # noqa: D401
        # Only validate scoped keys (nvapi-) for SERVICE_KEY blocking
        if self.client.config.app_key and self.client.config.app_key.startswith(SCOPED_KEY_PREFIX):
            key_details = self.client.authentication.get_sak_key_details(self.client.config.app_key)
            if getattr(key_details, "type", None) == "SERVICE_KEY":
                self.printer.print_error(self.SERVICE_KEY_ERROR_MESSAGE)
                return []

        # Legacy keys and personal scoped keys proceed normally
        orgs_list_pages = pagination_helper(self.connection, query, operation_name="get orgs")
        list_of_orgs = []
        for page in orgs_list_pages:
            list_of_orgs.extend(OrgListResponse(page).organizations)
        return list_of_orgs
