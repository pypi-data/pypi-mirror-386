#
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
# Holds all the constants used in the module
from collections import namedtuple
import multiprocessing
import platform
import signal
import sys

API_VERSION = "v2"
DATASET_SERVICE_API_VERSION = "v1"

DOCKER_API_VERSION = "1.23"
DOCKER_DAEMON_PORT = 443
TELEMETRY_TIMEOUT = 1
DOCKER_API_TIMEOUT = 60
DOCKER_ATTACH_TIMEOUT = 30 * 60
SECRET_API_VERSION = 0.0

CAS_URL_MAPPING = {
    "prod": "api.ngc.nvidia.com",
    "stg": "api.stg.ngc.nvidia.com",
    "canary": "api.canary.ngc.nvidia.com",
    "dev": "api.dev.ngc.nvidia.com",
}

CAS_TIMEOUT = 5 * 60 - 1

AUTH_URL_MAPPING = {
    "prod": "authn.nvidia.com",
    "canary": "authn.nvidia.com",
    "stg": "stg.authn.nvidia.com",
}

AUTH_TOKEN_SCOPE = {"prod": "ngc", "stg": "ngc-stg"}

PACKAGE_NAME = "ngc"

# For compliance with chardet's LGPL license
CHARDET_SUBSTITUTION_ENV_VAR = "NGC_CLI_CUSTOM_CHARDET_PATH"

LOG_PAGE_LIMIT = 10

LOG_PAGE_SIZE = 10000

LOG_REQUEST_LIMIT = 3

PAGE_SIZE = 500

LIST_LIMIT = 500

REQUEST_TIMEOUT_SECONDS = 30

DSS_QUERY_TIMEOUT_SECONDS = 10

LONG_MAX_VALUE = 9223372036854775807

INT_MAX_VALUE_32_BIT = 2147483647

WIN_MAX_PATH_LENGTH = 260

ASYNC_BATCH_SIZE = 500
SEMAPHORE_VALUE = 16
RESUME_DOWNLOAD_FILENAME = "files_to_download"

# Should never cache a function when running with pytest.
LRU_CACHE_SIZE = 0 if "pytest" in sys.modules else 256
FORMAT_TYPES = ["ascii", "csv", "json"]

# These are non-hidden roles. This is not filtered
# in help strings to only include whatever roles current user is able to assign.
# The latest available roles are received when calling `config set`, or when setting new command map.
# They are then saved onto meta_data file. Those latest roles are used in the help strings for `update-user`
# and `add-user` subcommands for the Org and Team commands.
USER_ROLES = [
    "BASE_COMMAND_ADMIN",
    "BASE_COMMAND_USER",
    "BASE_COMMAND_VIEWER",
    "FLEET_COMMAND_ADMIN",
    "FLEET_COMMAND_OPERATOR",
    "FLEET_COMMAND_VIEWER",
    "NVIDIA_AI_ENTERPRISE_VIEWER",
    "OMNIVERSE_ADMIN",
    "OMNIVERSE_READ",
    "OMNIVERSE_USER",
    "REGISTRY_ADMIN",
    "REGISTRY_READ",
    "REGISTRY_USER",
    "USER_ADMIN",
]

USER_ROLES_FORGE = [
    "FORGE_PROVIDER_ADMIN",
    "FORGE_TENANT_ADMIN",
]

# TODO: Once the migration of EGX_* to F_C_* roles is made, we should remove this as it will no longer be
#  necessary.
EGX_TO_FLEET_COMMAND_ROLE_MAPPING = {
    "EGX_ADMIN": "FLEET_COMMAND_ADMIN",
    "EGX_READ": "FLEET_COMMAND_VIEWER",
    "EGX_USER": "FLEET_COMMAND_OPERATOR",
}

FLEET_COMMAND_SERVICE_MAP = {
    "fleet-command",
    "apikey",
    "appconfig",
    "log",
    "settings",
    "usage",
    "component",
    "metric",
    "remote",
}

FORGE_SERVICE_MAP = {"forge"}

SERVICE_MAP = {
    "ACE": {"base-command", "ace"},
    "BASE_COMMAND_BANNER": {"alert"},
    "COLLECTION": {"registry", "collection", "label-set"},
    "CONTAINER": {"registry", "image", "label-set"},
    # `datamover` command piggybacking on the DATASET role
    "DATASET": {"base-command", "dataset", "import", "export", "datamover"},
    # All three F_C_* roles have these following four services.
    # All the F_C_* roles also have the "EGX" service.
    # So if a role has the following F_C_* services in allowedActions,
    # they have access to fleet-command commands.
    "FLEET_COMMAND_APPLICATION": FLEET_COMMAND_SERVICE_MAP.union({"application"}),
    "FLEET_COMMAND_DASHBOARD": FLEET_COMMAND_SERVICE_MAP.union({}),
    "FLEET_COMMAND_DEPLOYMENT": FLEET_COMMAND_SERVICE_MAP.union({"deployment"}),
    "FLEET_COMMAND_LOCATION": FLEET_COMMAND_SERVICE_MAP.union({"location"}),
    "FORGE_ALLOCATION": FORGE_SERVICE_MAP.union({"allocation"}),
    "FORGE_DASHBOARD": FORGE_SERVICE_MAP.union({}),
    # The role FORGE_TENANT_ADMIN has `FORGE_OPERATING_SYSTEM` service; FORGE_PROVIDER_ADMIN does not have this service.
    "FORGE_OPERATING_SYSTEM": FORGE_SERVICE_MAP.union(
        {
            "operating-system",
            "instance",
            "instance-type",
            "subnet",
            "tenant",
            "infiniband-partition",
            "vpc-prefix",
            "security-group",
        }
    ),
    "FORGE_RESOURCE": FORGE_SERVICE_MAP.union({"ipblock", "rule"}),
    "FORGE_SITE": FORGE_SERVICE_MAP.union({"site"}),
    # The role FORGE_PROVIDER_ADMIN has `FORGE_TENANT` service; FORGE_TENANT_ADMIN does not have this service.
    "FORGE_TENANT": FORGE_SERVICE_MAP.union(
        {
            "instance-type",
            "provider",
            "machine",
            "tenant-account",
            "ssh-key",
            "ssh-key-group",
        }
    ),
    "FORGE_VPC": FORGE_SERVICE_MAP.union({"vpc"}),
    "HELM": {"registry", "chart", "label-set"},
    "JOB": {"base-command", "job", "batch", "result", "resource"},
    "MODEL": {"registry", "model", "label-set"},
    "MODELSCRIPT": {"registry", "resource", "label-set"},
    "NVAIE": {},
    "OMNIVERSE": {},
    "ORG": {"org", "audit"},
    "TEAM": {"team", "audit"},
    "USER": {"user", "audit", "secret"},
    "WORKSPACE": {"base-command", "workspace", "import", "export"},
}
REMOTE_CONSOLE_USERNAME = "rcproxy"

REMOTE_CONSOLE_HOST = "localhost"

REMOTE_CONSOLE_RETRIES = 10

REMOTE_CONSOLE_SLEEP_CONSTANT = 10

PROXY_CHUNK_SIZE = 4 * 1024

OPENTELEMETRY_COMPONENT_NAME = "ngc-cli"

OPENTELEMETRY_COLLECTOR_HOST_MAPPING = {
    "prod": "prod.otel.kaizen.nvidia.com",
    "stg": "prod.otel.kaizen.nvidia.com",
    "dev": "stg.otel.kaizen.nvidia.com",
}

OPENTELEMETRY_COLLECTOR_PORT = 8282

OPENTELEMETRY_PRIVATE_TAGS = frozenset(["Authorization", "apikey"])

PROGRESS_BAR_STYLE_ENUM = ["DEFAULT", "ASCII", "NONE"]

# Update both TRANSFER_STATES_EXIT_CODE and TRANSFER_STATES for change
TRANSFER_STATES = {
    "NOT_STARTED": "Not Started",
    "COMPLETED": "Completed",
    "FAILED": "Failed",
    "TERMINATED": "Terminated",
    "IN_PROGRESS": "In Progress",
}

SECONDS_IN_MINUTE = 60

SECONDS_IN_HOUR = 3600

SECONDS_IN_DAY = 86400

KiB = 2**10
MiB = 2**20
GiB = 2**30
TiB = 2**40


def calc_max_threads(cores):  # noqa: D103
    # ~3 other threads exist during upload
    other_threads = 3
    threads = (2 * cores) - other_threads
    # 4 at minimum
    return max(threads, 4)


_cores = multiprocessing.cpu_count()
DEFAULT_UPLOAD_THREADS = max(_cores, 4)
MAX_UPLOAD_THREADS = calc_max_threads(_cores)
MAX_REQUEST_THREADS = _cores * 2

GRPC_SERVER_PORT = 7565
# NOTE: recommended grpc chunk size for streamed messages is 16-64KiB
# see: https://github.com/grpc/grpc.github.io/issues/371
GRPC_BUFFER_SIZE = 64 * KiB

MAX_HTTP_VERSION_FILE_SIZE = 1 * TiB  # Currently 1 tebibyte

# NOTE: For a general reference to common exit codes, see: http://tldp.org/LDP/abs/html/exitcodes.html
EXIT_CODES = {
    "SUCCESS": 0,
    "GENERAL_ERROR": 1,
    # argparse defaults to returning an error code of '2' for parsing problems.
    "MISUSE_OR_PARSING_ERROR": 2,
    # Fatal error signal (128 + 2)
    "TERMINATION_CTRL_C": 128 + signal.SIGINT,
    # See https://success.docker.com/article/what-causes-a-container-to-exit-with-code-137 for more information
    "DOCKER_CONTAINER_KILLED": 137,
    # Transfer-related exit codes
    "TRANSFER_FAILED": 3,
    "TRANSFER_TERMINATED": 4,
    "TRANSFER_INCOMPLETE": 5,
}

TRANSFER_STATES_EXIT_CODE = {
    "Not Started": EXIT_CODES["TRANSFER_INCOMPLETE"],
    "Completed": EXIT_CODES["SUCCESS"],
    "Failed": EXIT_CODES["TRANSFER_FAILED"],
    "Terminated": EXIT_CODES["TRANSFER_TERMINATED"],
    "In Progress": EXIT_CODES["TRANSFER_INCOMPLETE"],
}

UPLOAD_INVALID_FILE_PATTERN = r'^[^<>:;,?"*%|]+$'

# Used for unit testing
TEST_DOMAIN = "example.com"
TEST_URL = f"https://{TEST_DOMAIN}"


class _FeatureType(namedtuple("FeatureType", ["feature_name", "feature_rank"])):
    """This defines the type of the CLI to define what certain command/arguments are exposed to.
    The feature_rank defines the rank of the CLI type, smaller rank feature types are subsets of higher rank features
    In sense all the commands/arguments marked with smaller rank type will be available for higher rank types
    feature_name defines the name for the CLI type.
    """  # noqa: D205, D404

    def __gt__(self, other):
        return self.feature_rank > other.feature_rank

    def __ge__(self, other):
        return self.feature_rank >= other.feature_rank

    def __lt__(self, other):
        return self.feature_rank < other.feature_rank

    def __le__(self, other):
        return self.feature_rank <= other.feature_rank

    def __eq__(self, other):
        return self.feature_name == other.feature_name

    def __hash__(self):
        return hash((self.feature_name, self.feature_rank))

    def __ne__(self, other):
        return self.feature_name != other.feature_name

    def __str__(self):
        return self.feature_name


# TODO: TBD
SWIFTSTACK_STORAGE_CLUSTER = None
# TODO: Perform performance analysis on different dataset sizes and organizations to find good, general case values
S3_MULTIPART_UPLOAD_THRESHOLD = 8388608
S3_MULTIPART_UPLOAD_CHUNKSIZE = 8388608

CLEAR_LINE_CHAR = "\33[2K\r"

# Disable type can be used to disable something in CLI.
DISABLE_TYPE = _FeatureType("Disable", 0)
ENABLE_TYPE = _FeatureType("Enable", 1)
CONFIG_TYPE = _FeatureType("Config", 2)

# This defines the environment type of the CLI, ex. Staging, Canary, Production
BUILD_ENV = _FeatureType("Production", 0)
PRODUCTION_ENV = _FeatureType("Production", 3)
CANARY_ENV = _FeatureType("Canary", 2)
STAGING_ENV = _FeatureType("Staging", 1)
DEV_ENV = _FeatureType("Dev", 0)

BUILD_NAME_TO_SERVICE = {
    "dev": "ngcdev",
    "cli": "ngccli",
    "sdk": "ngcsdk",
}
# Defines mode which code is running under, ex. CLI, SDK
BUILD_TYPE = "sdk"

# Returns true when running in a frozen executable
PYINSTALLED = getattr(sys, "frozen", False)

VERSION_NUM = "4.8.2"

SERVICE_NAME = BUILD_NAME_TO_SERVICE.get(BUILD_TYPE, "ngcdev")
build_env_string = str(BUILD_ENV)
if BUILD_ENV == PRODUCTION_ENV:
    build_env_string = ""
USER_AGENT = f"{SERVICE_NAME}/{VERSION_NUM} {build_env_string} {platform.system().lower()}-{platform.machine()}"

# `ngc version` command requires these constants
VERSION_UPGRADE_CONSTANTS = {
    "CAN_RESOURCE_NAME": "ngc_cli_can",
    "DEV_RESOURCE_NAME": "ngc_cli_dev",
    "PROD_RESOURCE_NAME": "ngc_cli",
    "RESOURCE_LINUX_ARM64_FILE": "ngccli_arm64.zip",
    "RESOURCE_LINUX_FILE": "ngccli_linux.zip",
    "RESOURCE_MAC_INTEL_FILE": "ngccli_mac_intel.pkg",
    "RESOURCE_MAC_ARM64_FILE": "ngccli_mac_arm.pkg",
    "RESOURCE_ORG_NAME": "nvidia",
    "RESOURCE_TEAM_NAME": "ngc-apps",
    "RESOURCE_WINDOWS_FILE": "ngccli_win_x86.exe",
    "RESOURCE_WINDOWS_64_FILE": "ngccli_win_amd64.exe",
    "USER_OS": platform.system(),
}
CATALOG_RESOURCE_NAMES = {
    BUILD_ENV: VERSION_UPGRADE_CONSTANTS.get("DEV_RESOURCE_NAME"),
    CANARY_ENV: VERSION_UPGRADE_CONSTANTS.get("CAN_RESOURCE_NAME"),
    PRODUCTION_ENV: VERSION_UPGRADE_CONSTANTS.get("PROD_RESOURCE_NAME"),
}

OS_FILE_NAMES = {
    "Darwin": {
        "x86_64": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_MAC_INTEL_FILE"),
        "arm64": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_MAC_ARM64_FILE"),
    },
    "Linux": {
        "aarch64": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_LINUX_ARM64_FILE"),
        "x86_64": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_LINUX_FILE"),
    },
    "Windows": {
        "AMD64": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_WINDOWS_64_FILE"),
        "x86": VERSION_UPGRADE_CONSTANTS.get("RESOURCE_WINDOWS_FILE"),
    },
}

DAYS_BEFORE_DISPLAYING_UPGRADE_MSG = 1

# The following constants are meant for Scope API Keys.
SCOPED_KEY_PREFIX = "nvapi-"
API_KEY_DEPRECATION_DATE = "2025-01-01::01:00:00"

# When the token is just about to expire, refresh the token.
# Trigger a refreshing of token when the amount of time left before token expires
# is 5 minutes (300 seconds).
RENEW_TOKEN_BEFORE_EXPIRATION = 300

# The following constants are meant for Starfleet Authentication
# The user's `starfleet_kas_email` is added to SF_DEVICE_ID when making requests.
# SF_DEVICE_ID = hashlib.sha256(USER_AGENT.encode()).hexdigest()
SF_DEVICE_ID = USER_AGENT

DEPRECATION_MAP = {
    "ngc dataset": "ngc base-command dataset",
    "ngc batch": "ngc base-command job",
    "ngc workspace": "ngc base-command workspace",
    "ngc ace": "ngc base-command ace",
    "ngc result": "ngc base-command result",
    "ngc pym": "ngc base-command quickstart",
}

EXTERNAL_IP_URLS = ["https://api.ipify.org", "https://checkip.amazonaws.com/", "https://ifconfig.co/ip"]

PRODUCT_NAMES = [
    "nvaie-vpaif",
    "nv-cloud-functions",
    "secrets-manager",
    "base-command-platform",
    "nv-ai-enterprise",
    "nvaie-igx-safety-add-on",
    "chipnemo-inference",
    "ai-foundations",
    "artifact-catalog",
    "riva-virtual-assistant",
    "nemo-llm-service",
    "monai",
    "tao",
    "omniverse-cloud",
    "picasso",
    "data-services",
    "bluefield-enterprise-sw",
    "nv-quantum-cloud",
    "nvaie-igx-yocto-add-on",
    "fleet-command",
    "forge",
    "riva-enterprise",
    "cuopt",
    "met",
    "bionemo-service",
    "iam",
    "nvaie-igx",
    "e2",
    "private-registry",
]

UMASK_GROUP_OTHERS_READ_EXECUTE = 0o022
