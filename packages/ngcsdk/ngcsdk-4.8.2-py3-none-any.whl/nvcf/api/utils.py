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
import logging
from typing import Optional

from nvcf.api.constants import (
    AWS_URL,
    DOCKERHUB_URL,
    NVCF_GRPC_URL_MAPPING,
    NVCF_URL_MAPPING,
    PUBLIC_ECR_URL,
)

from ngcbase.api.utils import AccessDeniedException, add_scheme
from ngcbase.constants import (
    CANARY_ENV,
    CAS_URL_MAPPING,
    DEV_ENV,
    PRODUCTION_ENV,
    STAGING_ENV,
)
from ngcbase.errors import ResourceNotFoundException
from ngcbase.util.file_utils import helm_format
from ngcbase.util.utils import get_environ_tag
from registry.api.chart import ChartAPI
from registry.api.utils import (
    ChartRegistryTarget,
    get_chart_url,
    get_nvcr_relative_url,
    ImageRegistryTarget,
    ModelRegistryTarget,
)

env_mapping = {PRODUCTION_ENV: "prod", CANARY_ENV: "canary", STAGING_ENV: "stg", DEV_ENV: "dev"}
logger = logging.getLogger(__name__)
UNAUTH_WARNING_STR = "Warning: Current API key couldn't get access to resource %s. Proceeding."

SUPPORTED_CONTAINER_REGISTRIES = [
    DOCKERHUB_URL,
    AWS_URL,
    PUBLIC_ECR_URL,
]


def get_registry_hostnames_per_environment():
    """Return the appropriate environment hostnames."""
    if get_environ_tag() == STAGING_ENV:
        return [
            "stg.nvcr.io",
            "api.stg.ngc.nvidia.com",
            "stg.helm.ngc.nvidia.com",
            "helm.stg.ngc.nvidia.com",
            DOCKERHUB_URL,
            PUBLIC_ECR_URL,
        ]

    return [
        "nvcr.io",
        "api.ngc.nvidia.com",
        "helm.ngc.nvidia.com",
        DOCKERHUB_URL,
        PUBLIC_ECR_URL,
    ]


def get_nvcf_url_per_environment() -> str:
    """Return the appropriate URL for NVCF direct calls."""
    tag = get_environ_tag()
    env = env_mapping.get(tag)
    return NVCF_URL_MAPPING[env]


def get_nvcf_grpc_url_per_environment() -> str:
    """Return the appropriate grpc URL for NVCF grpc calls."""
    tag = get_environ_tag()
    env = env_mapping.get(tag)
    return NVCF_GRPC_URL_MAPPING[env]


def get_cas_url(scheme: Optional[bool] = True) -> str:
    """Return URL for absolute model/resouce urls."""
    tag = get_environ_tag()
    env = env_mapping.get(tag)
    if not scheme:
        return CAS_URL_MAPPING[env]
    return add_scheme(CAS_URL_MAPPING[env])


def validate_transform_image(client, container_image: str) -> str:  # noqa: D103
    if any(registry in container_image for registry in SUPPORTED_CONTAINER_REGISTRIES):
        return container_image
    try:
        ImageRegistryTarget(container_image, org_required=True, tag_required=True)
        client.registry.image.info(container_image)
    except ResourceNotFoundException as e:
        raise ResourceNotFoundException(
            f"Container Image {container_image} not found in nvcr, use ngc registry image info"
            f" {container_image} to validate image information"
        ) from e
    except AccessDeniedException:
        logger.warning(UNAUTH_WARNING_STR, container_image)

    # Prepend NVCR.io if not included
    if "nvcr.io/" not in container_image:
        image_repo_url = get_nvcr_relative_url()
        container_image = f"{image_repo_url}/{container_image}"

    return container_image


def validate_transform_model(client, model: str) -> dict:  # noqa: D103
    override_name = ""
    if len(overrides := model.split(":")) == 3:
        override_name = overrides[0]
        model = f"{overrides[1]}:{overrides[2]}"

    mrt = ModelRegistryTarget(model, version_required=True)
    name = override_name if override_name else mrt.name

    try:
        client.registry.model.info(model)
    except AccessDeniedException:
        logger.warning(UNAUTH_WARNING_STR, model)

    model_uri = (
        f"{get_cas_url()}/v2/org/{mrt.org}/team/{mrt.team}/models/{mrt.name}/{mrt.version}/files"
        if mrt.team
        else f"{get_cas_url()}/v2/org/{mrt.org}/models/{mrt.name}/{mrt.version}/files"
    )
    return {"name": name, "version": mrt.version, "uri": model_uri}


def validate_transform_helm_chart(client, helm_chart: str) -> str:  # noqa: D103
    if helm_chart.startswith("oci://"):
        return helm_chart
    crt = ChartRegistryTarget(helm_chart, version_required=True)
    try:
        client.registry.chart.info_chart_version(helm_chart)
    except AccessDeniedException:
        logger.warning(UNAUTH_WARNING_STR, helm_chart)

    # pylint: disable=protected-access
    helm_chart = (
        f"{get_chart_url()}/{ChartAPI._get_helm_pull_endpoint(crt.org,crt.team,helm_format(crt.name, crt.version))}"
    )
    return helm_chart


def validate_transform_resource(client, resource: str) -> dict:  # noqa: D103
    mrt = ModelRegistryTarget(resource, version_required=True)
    try:
        client.registry.resource.info(resource)
    except AccessDeniedException:
        logger.warning(UNAUTH_WARNING_STR, resource)

    model_uri = (
        f"{get_cas_url()}/v2/org/{mrt.org}/team/{mrt.team}/resources/{mrt.name}/{mrt.version}/files"
        if mrt.team
        else f"{get_cas_url()}/v2/org/{mrt.org}/resources/{mrt.name}/{mrt.version}/files"
    )

    return {"name": mrt.name, "version": mrt.version, "uri": model_uri}
