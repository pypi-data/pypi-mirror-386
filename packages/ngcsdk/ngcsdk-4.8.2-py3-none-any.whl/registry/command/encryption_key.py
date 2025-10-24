#
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import logging
import sys

from ngcbase.command.clicommand import CLICommand
from ngcbase.constants import ENABLE_TYPE
from ngcbase.errors import NgcAPIError
from ngcbase.util.utils import confirm_remove
from registry.api.utils import SimpleRegistryTarget
from registry.command.registry import RegistryCommand
from registry.printer.encryption_key import EncryptionKeyPrinter

logger = logging.getLogger(__name__)


class EncryptionKeyCommand(RegistryCommand):
    """Encryption Key Commands for managing encryption keys in the registry.

    Encryption keys are used to lock models/resources at creation time or associate them
    while the model is empty. Guest mode usage is not allowed for encryption keys.
    """

    CMD_NAME = "encryption-key"
    HELP = "Encryption Key Commands"
    DESC = "Encryption Key Commands for managing encryption keys in the registry"
    CLI_HELP = ENABLE_TYPE

    def __init__(self, parser):
        super().__init__(parser)
        self.parser = parser
        assert self.client, "Client not properly initialized"
        self.config = self.client.config
        self.api = self.client.registry.encryption_key
        self.printer = EncryptionKeyPrinter(self.client.config)

    # Help text constants
    LIST_HELP = "List encryption keys accessible by the user. \
        Uses configured org and team scope by default. \
        Use --list-team to override team scope (including 'no-team' for org-level keys only). \
        Note: encryption keys are scoped to specific org/team combinations and cannot be used across different scopes."
    INFO_HELP = "Get encryption key details and associated artifacts. \
        Use --artifact-type to filter by specific type or show all supported types by default. \
        Encryption key format: [org/[team/]]keyid"
    REMOVE_HELP = "Remove encryption key and all associated artifacts (async operation). \
        Returns statusUrl for polling. Encryption key format: [org/[team/]]keyid"
    DISASSOCIATE_HELP = "Disassociate models from encryption keys (async operation). \
        Returns statusUrl for polling. Model format: org/[team/]model_name"
    STATUS_HELP = "Get status of encryption key workflow operations using status URL"

    # Argument help text
    PATTERN_HELP = "Pattern to filter encryption keys by name (supports wildcards)"
    ENCRYPTION_KEY_ID_HELP = "Scoped encryption key target (format: [org/[team/]]keyid)"
    STATUS_URL_HELP = "Status URL to check status for (returned from async operations)"
    MODEL_HELP = "Model to disassociate from encryption key. Format: org/[team/]model_name"
    NO_WAIT_HELP = "Return status URL immediately without waiting for async operation to complete"
    LIST_TEAM_HELP = "Team name to list encryption keys from (uses configured org, overrides configured team). \
        Omit for org-level keys."

    # Supported artifact types for encryption keys
    SUPPORTED_ARTIFACT_TYPES = ["model"]  # Add more as backend supports them: ["model", "helm-chart", "resource"]

    @CLICommand.command(name="list", help=LIST_HELP, description=LIST_HELP)
    @CLICommand.arguments(
        "--list-team",
        metavar="<team_name>",
        help=LIST_TEAM_HELP,
        type=str,
        default=None,
    )
    def list(self, args):
        """List encryption keys accessible by the user in the current org/team scope.

        Unlike other artifacts, encryption keys are scoped to specific org/team combinations
        and cannot be used across different scopes. Results are limited to the currently
        configured auth org and team.

        """
        encryption_keys = self.api.list(team_name=args.list_team)
        list_org = self.config.org_name
        list_team = args.list_team or self.config.team_name

        logger.debug("Listing encryption keys for org/team: %s/%s", list_org, list_team)
        for key in encryption_keys.get("encryptionKeys", []):
            key["encryptionKey"] = f"{list_org}/{list_team + '/' if list_team else ''}{key['encryptionKeyId']}"
        self.printer.print_encryption_key_list(encryption_keys)

    @CLICommand.command(name="info", help=INFO_HELP, description=INFO_HELP)
    @CLICommand.arguments(
        "encryption_key_target",
        metavar="<encryption_key_target>",
        help=ENCRYPTION_KEY_ID_HELP,
        type=str,
    )
    @CLICommand.arguments(
        "--artifact-type",
        metavar="<artifact_type>",
        help="Filter artifacts by types. If not specified, shows all supported types.",
        type=str,
        nargs="*",
        default=["model"],
        action="append",
        choices=SUPPORTED_ARTIFACT_TYPES,
    )
    def info(self, args):
        """Get encryption key details and associated artifacts.

        Args:
            args: Command arguments containing key name and optional artifact type
        """
        target = SimpleRegistryTarget(args.encryption_key_target, org_required=True, name_required=True)

        encryption_key_info = {"artifacts": []}
        for art_type in args.artifact_type or self.SUPPORTED_ARTIFACT_TYPES:
            type_info = self.api.info(encryption_key_id=args.encryption_key_target, artifact_type=art_type)

            if hasattr(type_info, "artifacts") and type_info.artifacts:
                for art in type_info.artifacts:
                    if target.team:
                        art["name"] = f"{target.org}/{target.team}/{art['name']}"
                    else:
                        art["name"] = f"{target.org}/{art['name']}"
                encryption_key_info["artifacts"].extend(type_info.artifacts)

        encryption_key_info["encryptionKey"] = args.encryption_key_target
        self.printer.print_encryption_key_info(encryption_key_info, target.org, target.team)

    @CLICommand.command(name="remove", help=REMOVE_HELP, description=REMOVE_HELP)
    @CLICommand.arguments(
        "encryption_key_target",
        metavar="<encryption_key_target>",
        help=ENCRYPTION_KEY_ID_HELP,
        type=str,
        nargs="+",
    )
    @CLICommand.arguments(
        "--no-wait",
        help=NO_WAIT_HELP,
        action="store_true",
        default=False,
    )
    @CLICommand.arguments(
        "-y",
        "--yes",
        help="Automatically say yes to all interactive questions.",
        dest="default_yes",
        action="store_true",
    )
    def remove(self, args):
        """Remove encryption key and all associated artifacts.

        This is an async operation that removes the encryption key and all
        associated artifacts. By default, waits for completion.
        Use --no-wait flag to return immediately with statusUrl.

        Args:
            args: Command arguments containing key names and no-wait flag
        """
        # Confirm removal before proceeding
        list_of_keys = ", ".join(args.encryption_key_target)
        confirm_remove(printer=self.printer, target=f"encryption key(s) '{list_of_keys}'", default=args.default_yes)

        workflow_results = []
        for encryption_key_target in args.encryption_key_target:
            result = {
                "encryptionKey": encryption_key_target,
                "statusUrl": None,
                "status": "initiated",
            }
            try:
                api_response = self.api.remove_async(
                    encryption_key_id=encryption_key_target,
                )
                result["statusUrl"] = api_response.get(
                    "statusUrl", RuntimeError("No status URL returned from async operation")
                )
            except NgcAPIError as e:
                if e.response.status_code == 204 and "blank or malformed" in str(e):
                    result["status"] = "completed"
                    result["message"] = "Encryption key removed successfully"
                else:
                    result["status"] = "error"
                    result["error"] = str(e)
            except Exception as e:  # pylint: disable=broad-except
                result["status"] = "error"
                result["error"] = str(e)
            workflow_results.append(result)

        if args.no_wait:
            self.printer.print_remove_results(workflow_results)
            if any(r.get("status") == "error" for r in workflow_results):
                sys.exit(1)
            return

        for workflow_result in workflow_results:
            try:
                if workflow_result["status"] == "initiated":
                    self.api.wait_for_completion(status_url=workflow_result["statusUrl"])
                    workflow_result["status"] = "completed"
            except TimeoutError:
                workflow_result["status"] = "timeout"
                workflow_result["message"] = "Operation timed out but is still running"
            except Exception as e:  # pylint: disable=broad-except
                workflow_result["status"] = "error"
                workflow_result["error"] = str(e)

        self.printer.print_remove_results(workflow_results)

        if any(r.get("status") == "error" for r in workflow_results):
            sys.exit(1)

    @CLICommand.command(name="disassociate", help=DISASSOCIATE_HELP, description=DISASSOCIATE_HELP)
    @CLICommand.arguments(
        "--model",
        metavar="<model>",
        help=MODEL_HELP,
        type=str,
        default=None,
        action="append",
        required=True,
    )
    @CLICommand.arguments(
        "--no-wait",
        help=NO_WAIT_HELP,
        action="store_true",
        default=False,
    )
    @CLICommand.arguments(
        "-y",
        "--yes",
        help="Automatically say yes to all interactive questions.",
        dest="default_yes",
        action="store_true",
    )
    def disassociate(self, args):
        """Disassociate models from encryption keys.

        This is an async operation that disassociates models from their encryption keys.
        By default, waits for completion. Use --no-wait flag to return immediately with statusUrl.

        Args:
            args: Command arguments containing model list and no-wait flag
        """
        # Confirm disassociation before proceeding
        list_of_models = ",".join(args.model)
        if args.model:
            confirm_remove(printer=self.printer, target=f"model {list_of_models}", default=args.default_yes)

        workflow_results = []
        for model in args.model:
            result = {"artifactType": "model", "artifactName": model, "statusUrl": None, "status": "initiated"}
            try:
                api_response = self.api.disassociate_async(model)
                result["statusUrl"] = api_response.get("statusUrl", "Unknown")
            except Exception as e:  # pylint: disable=broad-except
                result["status"] = "error"
                result["error"] = str(e)
            workflow_results.append(result)

        if args.no_wait:
            self.printer.print_disassociate_results(workflow_results)
            if any(r.get("status") == "error" for r in workflow_results):
                sys.exit(1)
            return

        for workflow_result in workflow_results:
            try:
                if workflow_result["status"] == "initiated":
                    self.api.wait_for_completion(status_url=workflow_result["statusUrl"])
                    workflow_result["status"] = "completed"
            except TimeoutError:
                workflow_result["status"] = "timeout"
                workflow_result["message"] = "Operation timed out but is still running"
            except Exception as e:  # pylint: disable=broad-except
                workflow_result["status"] = "error"
                workflow_result["error"] = str(e)

        self.printer.print_disassociate_results(workflow_results)

        if any(r.get("status") == "error" for r in workflow_results):
            sys.exit(1)

    @CLICommand.command(name="status", help=STATUS_HELP, description=STATUS_HELP)
    @CLICommand.arguments(
        "status_url",
        metavar="<status_url>",
        help=STATUS_URL_HELP,
        type=str,
        nargs="+",
    )
    def status(self, args):
        """Get status of encryption key workflow operations using status URLs.

        Args:
            args: Command arguments containing status URLs
        """
        status_results = []
        for status_url in set(args.status_url):
            result = {"statusUrl": status_url, "status": "queried"}
            try:
                workflow_status = self.api.status(status_url=status_url)
                result.update(workflow_status)
            except Exception as e:  # pylint: disable=broad-except
                result["status"] = "error"
                result["error"] = str(e)
            status_results.append(result)

        self.printer.print_status_results(status_results)

        if any(r.get("status") == "error" for r in status_results):
            sys.exit(1)
