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

from fnmatch import fnmatch
import json
import re
from typing import Any, Dict, Optional, TYPE_CHECKING, Union

from nvcf.api.authorization import FunctionAuthorizationAPI
from nvcf.api.deploy import DeployAPI
from nvcf.api.function_instance import FunctionInstanceAPI
from nvcf.api.utils import (
    validate_transform_helm_chart,
    validate_transform_image,
    validate_transform_model,
    validate_transform_resource,
)

from ngcbase.api.utils import DotDict
from ngcbase.errors import InvalidArgumentError, NgcException
from ngcbase.util.utils import extra_args, parse_key_value_pairs

if TYPE_CHECKING:
    import ngcsdk

    import ngccli.api.apiclient

    Client = Union[ngccli.api.apiclient.APIClient, ngcsdk.APIClient]


class FunctionAPI:  # noqa: D101
    def __init__(self, api_client) -> None:
        self.connection = api_client.connection
        self.config = api_client.config
        self.client = api_client

    @property
    def deployments(self):  # noqa: D102
        return DeployAPI(api_client=self.client)

    @property
    def instances(self):  # noqa: D102
        return FunctionInstanceAPI(api_client=self.client)

    @property
    def authorizations(self):  # noqa: D102
        return FunctionAuthorizationAPI(api_client=self.client)

    @staticmethod
    def _construct_function_ep(
        org_name: str,
        team_name: Optional[str] = None,
        function_id: Optional[str] = None,
        function_version_id: Optional[str] = None,
        *,
        secret: bool = False,
        rate_limit: bool = False,
    ) -> str:
        parts = ["v2/orgs", org_name]
        if team_name:
            parts.extend(["teams", team_name])

        if secret:
            parts.extend(["nvcf", "secrets", "functions"])
        elif rate_limit:
            parts.extend(["nvcf", "ratelimit", "functions"])
        else:
            parts.extend(["nvcf", "functions"])

        if function_id:
            parts.extend([function_id, "versions"])

        if function_version_id:
            parts.append(function_version_id)

        return "/".join(parts)

    @extra_args
    def list(
        self,
        function_id: Optional[str] = None,
        name_pattern: Optional[str] = None,
        access_filter: Optional[list[str]] = None,
    ) -> DotDict:
        """List functions available to the organization. Currently set.

        Args:
            function_id: Optional parameter to list only versions of a specific function. Defaults to None.
            name_pattern: Optional parameter to filter functions that contain this name. Supports wildcards.
            access_filter: Optional parameter to filter functions by their access
            to the account to ["private","public", "authorized"].

        Returns:
            dict: Keyed List of Functions.
        """
        self.config.validate_configuration(csv_allowed=True)
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id)
        if access_filter:
            query = "?visibility=" + ",".join(access_filter)
            url += query
        response = self.connection.make_api_request(
            "GET",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="list function",
        )
        if name_pattern:
            response = {
                "functions": [fn for fn in response.get("functions", []) if fnmatch(fn.get("name"), name_pattern)]
            }
        return DotDict(response)

    @extra_args
    def info(self, function_id: str, function_version_id: str) -> DotDict:
        """Get information about a given function version.

        Args:
            function_id: Function's ID.
            function_version_id: Function's version ID.

        Returns:
            DotDict: JSON Response of NVCF function information.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id, function_version_id)
        response = self.connection.make_api_request(
            "GET",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="get function",
        )
        return DotDict(response)

    @extra_args
    def delete(self, function_id: str, function_version_id: str):
        """Delete a function version id.

        Args:
            function_id: Function's ID.
            function_version_id: Function's version ID.

        Returns:
            DotDict: JSON Response of NVCF function information.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id, function_version_id)
        self.connection.make_api_request(
            "DELETE",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="delete function",
            json_response=False,
        )

    @extra_args
    def create(
        self,
        name: str,
        inference_url: str,
        health_uri: Optional[str] = None,
        container_image: Optional[str] = None,
        helm_chart: Optional[str] = None,
        helm_chart_service: Optional[str] = None,
        models: Optional[list[str]] = None,
        function_id: Optional[str] = None,
        inference_port: Optional[int] = None,
        container_args: Optional[str] = None,
        api_body_format: Optional[str] = None,
        container_environment_variables: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        resources: Optional[list[str]] = None,
        *,
        function_type: str = "DEFAULT",
        health_expected_status_code: Optional[int] = None,
        health_port: Optional[int] = None,
        health_timeout: Optional[str] = None,
        health_protocol: Optional[str] = None,
        description: Optional[str] = None,
        secrets: Optional[list[str]] = None,
        json_secrets: Optional[list[tuple[str, bytes]]] = None,
        logs_telemetry_id: Optional[str] = None,
        metrics_telemetry_id: Optional[str] = None,
        traces_telemetry_id: Optional[str] = None,
        rate_limit_pattern: Optional[str] = None,
        rate_limit_exempt_nca_ids: Optional[list[str]] = None,
        rate_limit_sync_check: Optional[bool] = None,
    ) -> DotDict:
        """Create a function with the input specification provided by input.

        Args:
            name: Display name of the function.
            inference_url: Endpoint you wish to use to do invocations.
            health_uri: Health endpoint for inferencing
            container_image: Container Image.
            models: NGC models.
                In form [override_name:]model
            helm_chart: Helm Chart URL.
            helm_chart_service: Only necessary when helm chart is specified.
            function_id: If provided, generate another version of the same function.
            inference_port: Optional port override which inference is forwarded to.
            container_args: Optional list of arguments to provide to container.
            api_body_format: Optional body format to use.
            container_environment_variables: List of key pair values to pass as variables to container.
                In form ["key1:value1", "key2:value2"]
            tags: Optional list of tags to create the function with.
            resources: Optional list of resources.

        Keyword Args:
            function_type: Used to indicate a streaming function, defaults to DEFAULT.
            health_port: Port number where the health listener is running.
            health_protocol: HTTP/gPRC protocol type for health endpoint. Choices ["HTTP, gRPC"].
            health_timeout: ISO 8601 duration string in PnDTnHnMn.nS format.
            health_expected_status_code: Expected return status code considered as successful.
            description: Optional function/version description.
            secrets: Optional secret key/value pairs.
                In form ["key1:value1", "key2:value2"]
            json_secrets: Optional secret key/value pairs.
                In form [("key", {"jsonkey":1, "jsonkey2":{"nestedkey1":"nestedvalue"}}]
            logs_telemetry_id: UUID of telemetry log endpoint to map to function.
            metrics_telemetry_id: UUID of telemetry metrics endpoint to map to function.
            traces_telemetry_id: UUID of telemetry traces endpoint to map to function.
            rate_limit_pattern: Rate limit, format NUMBER-S|M|H|D, ex: 3-S.
            rate_limit_exempt_nca_ids: exempt NCA Ids.
            rate_limit_sync_check: Rate limit sync check.

        Raises:
            InvalidArgumentError: If neither container image, models, or helm chart is provided, this is thrown.
            ResourceNotFoundException: If the image or model or helm chart cannot be found.

        Returns:
            DotDict: Function Response provided by NVCF
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id)

        if helm_chart and container_image:
            raise InvalidArgumentError("Can not include helm chart with image")

        if not models and not container_image and not helm_chart:
            raise InvalidArgumentError("Must include either models and/or a container image or helm chart")

        if not rate_limit_pattern and (rate_limit_exempt_nca_ids or rate_limit_sync_check):
            raise InvalidArgumentError("Must include rate limit pattern with rate limit params")

        if container_image:
            container_image = validate_transform_image(self.client, container_image)

        function_models: list[dict] = []
        for model in models or []:
            function_models.append(validate_transform_model(self.client, model))

        if helm_chart:
            if not helm_chart_service:
                raise InvalidArgumentError("Must include a helm chart service name if helm chart is included")
            helm_chart = validate_transform_helm_chart(self.client, helm_chart)

        function_resources: list[dict] = []
        for resource in resources or []:
            function_resources.append(validate_transform_resource(self.client, resource))

        function_container_env_variables: list[dict] = []
        if container_environment_variables:
            function_container_env_variables = [
                {"key": k, "value": v} for k, v in parse_key_value_pairs(container_environment_variables).items()
            ]

        function_secrets: list[dict] = []
        if secrets:
            function_secrets = [{"name": k, "value": v} for k, v in parse_key_value_pairs(secrets).items()]

        if json_secrets:
            for k, v in json_secrets:
                try:
                    function_secrets.append({"name": k, "value": json.loads(v)})
                except (json.JSONDecodeError, TypeError) as e:
                    raise NgcException(f"Invalid JSON in secret {k}") from e

        payload: dict[str, Any] = {
            "name": name,
            "inferenceUrl": inference_url,
            "inferencePort": inference_port,
            "containerArgs": container_args,
            "containerEnvironment": function_container_env_variables,
            "models": function_models,
            "functionType": function_type,
            "containerImage": container_image,
            "apiBodyFormat": api_body_format,
            "healthUri": health_uri,
            "helmChart": helm_chart,
            "helmChartServiceName": helm_chart_service,
            "tags": tags,
            "resources": function_resources,
            "description": description,
            "secrets": function_secrets,
        }
        health = {
            "protocol": health_protocol,
            "uri": health_uri,
            "timeout": health_timeout,
            "port": health_port,
            "expectedStatusCode": health_expected_status_code,
        }
        health = {key: val for key, val in health.items() if val}

        # Old `healthUri` field is deprecated, but now belongs in the health object.
        if len(health) == 1 and "uri" in health:
            payload["healthUri"] = health_uri
        else:
            payload["health"] = health

        if logs_telemetry_id or metrics_telemetry_id or traces_telemetry_id:
            payload["telemetries"] = {
                "logsTelemetryId": logs_telemetry_id,
                "metricsTelemetryId": metrics_telemetry_id,
                "tracesTelemetryId": traces_telemetry_id,
            }

        if rate_limit_pattern:
            rate_limit = {
                "rateLimit": rate_limit_pattern,
                "exemptedNcaIds": rate_limit_exempt_nca_ids,
                "syncCheck": rate_limit_sync_check,
            }
            payload["rateLimit"] = {key: val for key, val in rate_limit.items() if val}

        payload = {key: val for key, val in payload.items() if val}

        response = self.connection.make_api_request(
            "POST",
            url,
            payload=json.dumps(payload),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="create function",
        )
        return DotDict(response)

    @extra_args
    def update_rate_limit(
        self,
        function_id: str,
        function_version_id: str,
        rate_limit_pattern: str,
        rate_limit_exempt_nca_ids: Optional[list[str]] = None,
        rate_limit_sync_check: Optional[bool] = None,
    ):
        """Update a given function's secrets.

        Args:
            function_id: Function's ID.
            function_version_id: Function's version ID.
            rate_limit_pattern: Rate limit, format NUMBER-S|M|H|D, ex: 3-S.
            rate_limit_exempt_nca_ids: exempt NCA Ids.
            rate_limit_sync_check: Rate limit sync check.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(
            org_name,
            team_name,
            function_id,
            function_version_id,
            rate_limit=True,
        )
        if not rate_limit_pattern or not re.match(r"^\d+-[SMHD]$", rate_limit_pattern):
            raise NgcException(f"Invalid rate limit: '{rate_limit_pattern}'. Valid format NUMBER-S|M|H|D.")

        payload: Dict[str, Any] = {
            "rateLimit": {
                "rateLimit": rate_limit_pattern,
                "exemptedNcaIds": rate_limit_exempt_nca_ids,
                "syncCheck": rate_limit_sync_check,
            }
        }

        self.connection.make_api_request(
            "PUT",
            url,
            payload=json.dumps(payload),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="update function rate limit",
            json_response=False,
        )

    @extra_args
    def remove_rate_limit(self, function_id: str, function_version_id: str):
        """Delete a function rate limit.

        Args:
            function_id: Function's ID.
            function_version_id: Function's version ID.
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id, function_version_id, rate_limit=True)
        self.connection.make_api_request(
            "DELETE",
            url,
            auth_org=org_name,
            auth_team=team_name,
            operation_name="delete function rate limit",
            json_response=False,
        )

    @extra_args
    def update_secrets(
        self,
        function_id: str,
        function_version_id: str,
        secrets: Optional[list[str]] = None,
        json_secrets: Optional[list[tuple[str, bytes]]] = None,
    ):
        """Update a given function's secrets.

        Args:
            function_id: Function's ID.
            function_version_id: Function's version ID.

            secrets: Optional secret key/value pairs.
                In form ["key1:value1", "key2:value2"]
            json_secrets: Optional secret key/value pairs.
                In form [("key", {"jsonkey":1, "jsonkey2":{"nestedkey1":"nestedvalue"}}]
        """
        self.config.validate_configuration()
        org_name: str = self.config.org_name
        team_name: Optional[str] = self.config.team_name
        url = self._construct_function_ep(org_name, team_name, function_id, function_version_id, secret=True)
        function_secrets: list[dict] = []

        if secrets:
            function_secrets = [{"name": k, "value": v} for k, v in parse_key_value_pairs(secrets).items()]
        if json_secrets:
            for k, v in json_secrets:
                try:
                    function_secrets.append({"name": k, "value": json.loads(v)})
                except (json.JSONDecodeError, TypeError) as exc:
                    raise NgcException(f"Invalid JSON in secret name {k}") from exc

        payload: dict[str, Any] = {
            "secrets": function_secrets,
        }
        self.connection.make_api_request(
            "PUT",
            url,
            payload=json.dumps(payload),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="update function secrets",
            json_response=False,
        )
