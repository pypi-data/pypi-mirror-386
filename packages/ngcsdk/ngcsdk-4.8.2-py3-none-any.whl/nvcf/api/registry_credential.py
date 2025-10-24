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
#
from __future__ import annotations

import base64
import json
from typing import Any, Literal, Optional, TYPE_CHECKING, Union

from nvcf.api.constants import (
    AWS_URL,
    DOCKERHUB_URL,
    ECR_PATTERN,
    NGC_HELM_URL,
    NGC_IMAGE_URL,
    NGC_URL,
    PUBLIC_ECR_URL,
)

from ngcbase.api.utils import DotDict
from ngcbase.errors import InvalidArgumentError, NgcException, ResourceNotFoundException

if TYPE_CHECKING:
    import ngcsdk

    import ngccli.api.apiclient

    Client = Union[ngccli.api.apiclient.APIClient, ngcsdk.APIClient]

REGISTRY_HOSTNAME = Literal[
    "helm.ngc.nvidia.com",
    "api.ngc.nvidia.com",
    "docker.io",
    "nvcr.io",
    "public.ecr.aws",
]
REGISTRY_TYPE = Literal[
    "CONTAINER",
    "RESOURCE",
    "MODEL",
    "HELM",
]

REGISTRY_TYPE_MAP: dict[str, list[str]] = {
    "CONTAINER": [
        NGC_IMAGE_URL,
        PUBLIC_ECR_URL,
        DOCKERHUB_URL,
        "stg.nvcr.io",
    ],
    "RESOURCE": [
        NGC_URL,
        "api.stg.ngc.nvidia.com",
    ],
    "MODEL": [
        NGC_URL,
        "api.stg.ngc.nvidia.com",
    ],
    "HELM": [
        NGC_HELM_URL,
        PUBLIC_ECR_URL,
        DOCKERHUB_URL,
        "stg.helm.ngc.nvidia.com",
    ],
}


class RegistryCredentialAPI:  # noqa: D101
    def __init__(self, api_client) -> None:
        self.connection = api_client.connection
        self.config = api_client.config
        self.client = api_client

    @staticmethod
    def _encode_creds(
        hostname: str,
        key: str,
        username: Optional[str] = None,
        aws_access_key: Optional[str] = None,
    ) -> bytes:
        creds = ""
        if hostname in [DOCKERHUB_URL]:
            if not username:
                raise InvalidArgumentError("Must provide username")
            creds = f"{username}:{key}"
        elif hostname in [PUBLIC_ECR_URL] or AWS_URL in hostname:
            if not aws_access_key:
                raise InvalidArgumentError("Must provide aws_access_key")
            creds = f"{aws_access_key}:{key}"
        else:
            creds = f"$oauthtoken:{key}"
        return base64.b64encode(bytes(creds, "utf-8"))

    @staticmethod
    def _construct_registry_credentials_ep(
        org_name: str,
        team_name: Optional[str] = None,
        registry_credentials_id: Optional[str] = None,
    ) -> str:
        parts = ["v2/orgs", org_name]
        if team_name:
            parts.extend(["teams", team_name])
        parts.extend(["nvcf", "registry-credentials"])
        if registry_credentials_id:
            parts.append(registry_credentials_id)
        return "/".join(parts)

    def info(self, id: str) -> DotDict:
        """Info about registry credentials.

        Returns:
            DotDict: Registry Credential Info.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_registry_credentials_ep(org_name, team_name, id)
        response = self.connection.make_api_request(
            "GET",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="info registry-credential",
        )
        return DotDict(response)

    def list(self) -> DotDict:
        """List Telemetry endpoints.

        Returns:
            DotDict: Keyed List of Functions.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_registry_credentials_ep(org_name, team_name)
        response = self.connection.make_api_request(
            "GET",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="list registry credential",
        )
        return DotDict(response)

    def create(
        self,
        name: str,
        hostname: REGISTRY_HOSTNAME,
        types: list[REGISTRY_TYPE],
        key: str,
        *,
        aws_access_key: Optional[str] = None,
        username: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> DotDict:
        """Add registry credentials.

        Args:
            name: Registry credentials name.
            hostname: Registry hostname.
            types: Artifact type.
            key: Registry credentials key.

        Keyword Args:
            username: Optional username key for certain hostnames.
            aws_access_key: Optional access_key for certain hostnames.
            description: Optional registry credentials.
            tags: Optional tags for registry credentials.

        Returns:
            DotDict: information on created registry credential.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_registry_credentials_ep(org_name, team_name)

        for type_ in types:
            if hostname in REGISTRY_TYPE_MAP[type_]:
                continue
            if type_ in ["CONTAINER", "HELM"] and ECR_PATTERN.match(hostname):
                continue
            raise InvalidArgumentError(f"'{type_}' not available for hostname {hostname}")

        creds = self._encode_creds(
            hostname=hostname,
            key=key,
            username=username,
            aws_access_key=aws_access_key,
        )
        payload: dict[str, Any] = {
            "registryHostname": hostname,
            "tags": tags,
            "artifactTypes": types,
            "description": description,
            "secret": {"name": name, "value": creds.decode("utf-8")},
        }
        payload = {key: val for key, val in payload.items() if val}

        response = self.connection.make_api_request(
            "POST",
            url,
            payload=json.dumps(payload),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="create registry-credential",
        )
        return DotDict(response)

    def update(
        self,
        id: str,
        key: str,
        *,
        username: Optional[str] = None,
        aws_access_key: Optional[str] = None,
    ) -> DotDict:
        """Update registry credentials.

        Args:
            id: Registry credentials UUID.
            key: Registry credentials key.

        Keyword Args:
            username: Optional username for certain hostnames.
            aws_access_key: Optional access_key for certain hostnames.

        Returns:
            DotDict: information on created registry credential.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_registry_credentials_ep(org_name, team_name, id)

        registry_credential = self.info(id)
        if registry_credential.registryCredential.provisionedBy == "SYSTEM":
            raise NgcException("Can not update a system provisioned credential")

        name, hostname = (
            registry_credential.registryCredential.registryCredentialName,
            registry_credential.registryCredential.registryHostname,
        )
        creds = self._encode_creds(
            hostname=hostname,
            key=key,
            username=username,
            aws_access_key=aws_access_key,
        )
        payload: dict[str, Any] = {"secret": {"name": name, "value": creds.decode("utf-8")}}
        response = self.connection.make_api_request(
            "PATCH",
            url,
            payload=json.dumps(payload),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="update registry-credential",
        )
        return DotDict(response)

    def delete(self, id: str):
        """Delete registry credentials.

        Args:
        id: UUID of registry credentials endpoint.
        """
        self.config.validate_configuration()
        try:
            registry_creds = self.info(id)
            if registry_creds.registryCredential.provisionedBy == "SYSTEM":
                raise NgcException("Can not delete a system provisioned credential")
        except ResourceNotFoundException as e:
            raise NgcException(f"Registry credential {id} doesn't exist") from e

        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_registry_credentials_ep(
            org_name,
            team_name,
            id,
        )
        self.connection.make_api_request(
            "DELETE",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="delete registry-credential",
            json_response=False,
        )
