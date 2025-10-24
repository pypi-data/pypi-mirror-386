#
# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
import argparse
from builtins import int
from collections.abc import Iterable
import datetime
import http
from itertools import chain
import logging
from operator import xor
import os
from typing import Callable, List, Literal, Optional, Union
from urllib.parse import urlencode

from ngcbase.api.pagination import pagination_helper_page_reference_iter_total_pages
from ngcbase.constants import CAS_TIMEOUT
from ngcbase.errors import (
    InvalidArgumentError,
    NgcAPIError,
    NgcException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from ngcbase.printer.transfer import TransferPrinter
from ngcbase.tracing import TracedSession
from ngcbase.transfer import async_download, async_workers
from ngcbase.transfer.utils import get_download_files, use_noncanonical_url
from ngcbase.util.file_utils import get_file_contents, tree_size_and_count
from ngcbase.util.utils import extra_args, format_org_team
from registry.api.utils import (
    add_credentials_to_request,
    apply_labels_update,
    filter_version_list,
    get_auth_org_and_team,
    get_label_set_labels,
    handle_public_dataset_no_args,
    make_transfer_result,
    ModelRegistryTarget,
    SimpleRegistryTarget,
    validate_destination,
    verify_link_type,
)

# pylint: disable=W0001
from registry.data.model.ArtifactAttribute import ArtifactAttribute
from registry.data.model.Model import Model
from registry.data.model.ModelCreateRequest import ModelCreateRequest
from registry.data.model.ModelResponse import ModelResponse
from registry.data.model.ModelUpdateRequest import ModelUpdateRequest
from registry.data.model.ModelVersion import ModelVersion
from registry.data.model.ModelVersionCreateRequest import ModelVersionCreateRequest
from registry.data.model.ModelVersionFileListResponse import (
    ModelVersionFileListResponse,
)
from registry.data.model.ModelVersionListResponse import ModelVersionListResponse
from registry.data.model.ModelVersionResponse import ModelVersionResponse
from registry.data.model.ModelVersionUpdateRequest import ModelVersionUpdateRequest
from registry.data.publishing.LicenseMetadata import LicenseMetadata
from registry.printer.model import ModelPrinter
from registry.transformer.image import RepositorySearchTransformer

logger = logging.getLogger(__name__)

PAGE_SIZE = 1000

ENDPOINT_VERSION = "v2"


class ModelAPI:  # noqa: D101
    def __init__(self, api_client):
        self.config = api_client.config
        self.connection = api_client.connection
        self.client = api_client
        self.transfer_printer = TransferPrinter(api_client.config)
        self.printer = ModelPrinter(api_client.config)
        self.resource_type = "MODEL"

    # PUBLIC FUNCTIONS
    @extra_args
    def download_version(
        self,
        target: str,
        destination: Optional[str] = ".",
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback_func: Optional[Callable[[int, int, int, int, int, int], None]] = None,
    ):
        """Download the specified model version.

        Args:
            target: Full model name. org/[team/]name[:version]
            destination: Description of model. Defaults to ".".
            file_patterns: Inclusive filter of model files. Defaults to None.
            exclude_patterns: Eclusive filter of model files. Defaults to None.
            progress_callback_func (Optional[Callable[[int, int, int, int, int, int], None]]):
                A callback function that accepts six integers representing
                completed_bytes, failed_bytes, total_bytes, completed_count,
                failed_count, and total_count respectively. If provided,
                this function will be called to report progress periodically.
                If set to None, progress updates will not be reported.

        Returns:
            DotDict: A dictionary-like object with attribute access, containing the following fields:
            - `transfer_id` (str): Unique identifier for the transfer session.
            - `status` (str): Final status of the transfer (e.g., "completed", "failed").
            - `path` (str): Local path to the directory where the data was downloaded to.
            - `duration_seconds` (float): Total duration of the transfer in seconds.
            - `completed_count` (int): Number of files successfully transferred.
            - `completed_bytes` (int): Total number of bytes successfully transferred.
            - `started_at` (str): ISO 8601 timestamp when the transfer began.
            - `ended_at` (str): ISO 8601 timestamp when the transfer ended.

        Raises:
            NgcException: If unable to download.
            ResourceNotFoundException: If model is not found.
        """
        self.config.validate_configuration(guest_mode_allowed=True)
        # non-list, use org/team from target
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=False)

        model_response = self.get(mrt.org, mrt.team, mrt.name)
        if not mrt.version:
            mrt.version = self._get_latest_version_from_artifact_response(model_response)
            target += f":{mrt.version}"
            self.transfer_printer.print_ok(f"No version specified, downloading latest version: '{mrt.version}'.")

        download_dir = validate_destination(destination, mrt, mrt.name)
        try:
            version_resp = self.get_version(mrt.org, mrt.team, mrt.name, mrt.version)
            version_status = version_resp.modelVersion.status
            if version_status != "UPLOAD_COMPLETE":
                raise NgcException(f"'{target}' is not in state UPLOAD_COMPLETE.")
        except ResourceNotFoundException:
            raise ResourceNotFoundException(f"'{target}' could not be found.") from None
        self.transfer_printer.print_download_message("Getting files to download...\n")
        try:
            all_files = list(self.list_files(target, mrt.org, mrt.team))
        except NgcAPIError as e:
            if e.response.status_code == http.HTTPStatus.PRECONDITION_FAILED:
                raise NgcException(f"{e}\nPlease accept required license(s) via the NGC UI.") from None
            raise e from None
        all_files_path_size = {f.path: f.sizeInBytes for f in all_files}
        dl_files, total_size = get_download_files(
            {f.path: f.sizeInBytes for f in all_files}, [], file_patterns, None, exclude_patterns
        )
        dl_files_with_size = {f: all_files_path_size.get(f, 0) for f in dl_files}
        paginated = not (file_patterns or exclude_patterns)
        if paginated:
            logger.debug("Downloading all files for model '%s' version '%s'", mrt.name, mrt.version)
        else:
            logger.debug("Downloading %s files for model '%s' version '%s'", len(dl_files), mrt.name, mrt.version)
        url = self.get_direct_download_URL(mrt.name, mrt.version, org=mrt.org, team=mrt.team)
        # Need to match the old output where the files are within a subfolder
        started_at = datetime.datetime.now()
        progress = async_download.direct_download_files(
            "model",
            mrt.name,
            mrt.org,
            mrt.team,
            mrt.version,
            url,
            paginated,
            dl_files_with_size,
            total_size,
            download_dir,
            self.client,
            progress_callback_func,
        )

        ended_at = datetime.datetime.now()
        xfer_id = f"{mrt.name}[version={mrt.version}]"

        return make_transfer_result(
            xfer_id,
            progress.status,
            download_dir,
            progress.completed_count,
            progress.completed_bytes,
            started_at,
            ended_at,
        )

    @extra_args
    def upload_version(
        self,
        target: str,
        source: Optional[str] = ".",
        gpu_model: Optional[str] = None,
        memory_footprint: Optional[str] = None,
        num_epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        accuracy_reached: Optional[float] = None,
        description: Optional[str] = None,
        link: Optional[str] = None,
        link_type: Optional[str] = None,
        dry_run: Optional[bool] = False,
        credential_files: Optional[List[str]] = None,
        metric_files: Optional[List[str]] = None,
        base_version: Optional[str] = None,
        progress_callback_func: Optional[Callable[[int, int, int, int, int, int], None]] = None,
        complete_version=True,
    ):
        """Upload a model version.

        Args:
            target: Full model name. org/[team/]name[:version]
            source: Source location of model. Defaults to the current directory.
            gpu_model: GPU model of model. Defaults to None.
            memory_footprint: Memory footprint of model. Defaults to None.
            num_epochs: Epoch number of model. Defaults to None.
            batch_size: Batch size of model. Defaults to None.
            accuracy_reached: Accuracy of model. Defaults to None.
            description: Description of model. Defaults to None.
            link: Link of model. Defaults to None.
            link_type: Link type of model. Defaults to None.
            dry_run: Is this a dry run. Defaults to False.
            credential_files: Credential files of model. Defaults to None.
            metric_files: Metric files of model. Defaults to None.
            base_version: Include all files from a base version.
                Files with same path are overwritten by source.
            progress_callback_func (Optional[Callable[[int, int, int, int, int, int], None]]):
                A callback function that accepts six integers representing
                completed_bytes, failed_bytes, total_bytes, completed_count,
                failed_count, and total_count respectively. If provided,
                this function will be called to report progress periodically.
                If set to None, progress updates will not be reported.
            complete_version: If all uploads are successful and complete_version is True, mark this version complete.

        Returns:
            DotDict: A dictionary-like object with attribute access, containing the following fields:
            - `transfer_id` (str): Unique identifier for the transfer session.
            - `status` (str): Final status of the transfer (e.g., "completed", "failed").
            - `path` (str): Local path to the directory where the data was uploaded from.
            - `duration_seconds` (float): Total duration of the transfer in seconds.
            - `completed_count` (int): Number of files successfully transferred.
            - `completed_bytes` (int): Total number of bytes successfully transferred.
            - `started_at` (str): ISO 8601 timestamp when the transfer began.
            - `ended_at` (str): ISO 8601 timestamp when the transfer ended.

        Raises:
            NgcException: If failed to upload model.
            argparse.ArgumentTypeError: If invalid input model name.
            ResourceAlreadyExistsException: If model resource already existed.
            ResourceNotFoundException: If model cannot be find.
        """
        self.config.validate_configuration()
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=True)

        transfer_path = os.path.abspath(source)
        if not os.path.exists(transfer_path):
            raise NgcException("The path: '{0}' does not exist.".format(transfer_path))

        verify_link_type(link_type)
        version_req = ModelVersionCreateRequest(
            {
                "versionId": mrt.version,
                "accuracyReached": accuracy_reached,
                "batchSize": batch_size,
                "description": description,
                "gpuModel": gpu_model,
                "memoryFootprint": memory_footprint,
                "numberOfEpochs": num_epochs,
            }
        )

        if link and link_type:
            version_req.otherContents = [ArtifactAttribute({"key": link_type, "value": link})]

        if xor(bool(link), bool(link_type)):
            raise argparse.ArgumentTypeError("Invalid arguments: --link and --link-type must be used together.")

        version_req = add_credentials_to_request(version_req, credential_files, metric_files)

        version_req.isValid()

        storage_version = self.validated_storage_version(mrt, version_req, base_version)

        if dry_run:
            self.transfer_printer.print_ok("Files to be uploaded:")
        transfer_size, file_count = tree_size_and_count(
            transfer_path,
            omit_links=False,
            print_paths=dry_run,
            dryrun_option=dry_run,
            check_max_size=True,
        )
        if dry_run:
            self.transfer_printer.print_upload_dry_run(transfer_size, file_count)
            return None

        started_at = datetime.datetime.now()
        try:
            progress = async_workers.upload_directory(
                self.client,
                transfer_path,
                mrt.name,
                mrt.version,
                mrt.org,
                mrt.team,
                "models",
                operation_name="model upload version",
                progress_callback_func=progress_callback_func,
                base_version=base_version,
                storage_version=storage_version,
            )

            ended_at = datetime.datetime.now()

            xfer_id = f"{mrt.name}[version={mrt.version}]"

            #                 complete_version=True
            # status      Completed    |    Other status
            # v1       upload_complete |      stash
            # v2       upload_complete |     no action

            #                complete_version=False
            # status      Completed    |    Other status
            # v1       stash           |      stash
            # v2       no action       |      no action

            is_v1 = storage_version == "V1"
            is_completed = progress.status == "Completed"

            if complete_version and is_completed:
                self._update_upload_complete(mrt.org, mrt.team, mrt.name, mrt.version)

            elif is_v1:
                self._stash_version(mrt.org, mrt.team, mrt.name, mrt.version)

            return make_transfer_result(
                xfer_id,
                progress.status,
                transfer_path,
                progress.completed_count,
                progress.completed_bytes,
                started_at,
                ended_at,
            )
        except async_workers.ModelVersionIntegrityError as e:
            self.remove_version(mrt.org, mrt.team, mrt.name, mrt.version)
            raise async_workers.ModelVersionIntegrityError(
                f"Model version '{target}' encryption scheme is lost, please retry later. {e}"
            ) from e

    def commit_version(self, target: str) -> ModelVersionResponse:
        """Commit a model version.

        Args:
            target: Full model name. org/[team/]name[:version]

        Raises:
            ResourceNotFoundException: If model is not found.
            ArgumentTypeError: If model version is not found.
            InvalidArgumentError: If model version does not have status UPLOAD_PENDING.

        """
        self.config.validate_configuration()
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=True)
        org_name = mrt.org
        team_name = mrt.team

        model_version = self.get_version(mrt.org, mrt.team, mrt.name, mrt.version)
        if model_version.modelVersion.status != "UPLOAD_PENDING":
            raise InvalidArgumentError("Model '{}' status is not UPLOAD_PENDING.".format(mrt)) from None

        return self._update_upload_complete(org_name, team_name, mrt.name, mrt.version)

    @extra_args
    def update(  # noqa: D417
        self,
        target: str,
        application: Optional[str] = None,
        framework: Optional[str] = None,
        model_format: Optional[str] = None,
        precision: Optional[str] = None,
        short_description: Optional[str] = None,
        description: Optional[str] = None,
        overview_filename: Optional[str] = None,
        bias_filename: Optional[str] = None,
        explainability_filename: Optional[str] = None,
        privacy_filename: Optional[str] = None,
        safety_security_filename: Optional[str] = None,
        display_name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        add_label: Optional[List[str]] = None,
        remove_label: Optional[List[str]] = None,
        label_set: Optional[List[str]] = None,
        logo: Optional[str] = None,
        public_dataset_name: Optional[str] = None,
        public_dataset_link: Optional[str] = None,
        public_dataset_license: Optional[str] = None,
        memory_footprint: Optional[str] = None,
        built_by: Optional[str] = None,
        publisher: Optional[str] = None,
        batch_size: Optional[int] = None,
        num_epochs: Optional[int] = None,
        accuracy_reached: Optional[float] = None,
        gpu_model: Optional[str] = None,
        set_latest: Optional[bool] = None,
    ) -> Union[Model, ModelVersion]:
        """Update a model or model version.

        Args:
            target: Full model name. org/[team/]name[:version]
            application: Application of model. Defaults to None.
            framework: Framework of model. Defaults to None.
            model_format: Format of model. Defaults to None.
            precision: Precision of model. Defaults to None.
            short_description: Short description of model. Defaults to None.
            description: Description of model. Defaults to None.
            overview_filename: Overview of model filename. Defaults to None.
            bias_filename: Bias filename of model. Defaults to None.
            explainability_filename: Explainability filename of model. Defaults to None.
            privacy_filename: Privacy filename of model. Defaults to None.
            safety_security_filename: Safety security filename of model. Defaults to None.
            display_name: Display name of model. Defaults to None.
            label (Lis: Label of model. Defaults to None.
            label_set (Lis: Label set of model. Defaults to None.
            logo: Logo of model. Defaults to None.
            public_dataset_name: Public dataset name of model. Defaults to None.
            public_dataset_link: Public dataset link of model. Defaults to None.
            public_dataset_license: Public dataset license of model. Defaults to None.
            memory_footprint: Memory footprint of model. Defaults to None.
            built_by: Time model is built by. Defaults to None.
            publisher: Model publisher. Defaults to None.
            batch_size: Model batch size. Defaults to None.
            num_epochs: Epoch number of model. Defaults to None.
            accuracy_reached: Accuracy of model. Defaults to None.
            gpu_model: GPU model of model. Defaults to None.
            set_latest: Model set latest. Defaults to None.

        Raises:
            ResourceNotFoundException: If model is not found
            ArgumentTypeError: If labels or label_set used along with add_label or remove_label.
        """
        self.config.validate_configuration(guest_mode_allowed=True)
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True)
        org_name = mrt.org
        team_name = mrt.team
        if (labels or label_set) and (add_label or remove_label):
            raise argparse.ArgumentTypeError(
                "Declaritive arguments `labels` or `label_set` "
                "cannot be used with imperative arguments `add_label` or `remove_label`"
            )

        if mrt.version:
            self._validate_update_version(locals())
            version_update_req = ModelVersionUpdateRequest(
                {
                    "accuracyReached": accuracy_reached,
                    "batchSize": batch_size,
                    "gpuModel": gpu_model,
                    "memoryFootprint": memory_footprint,
                    "numberOfEpochs": num_epochs,
                    "description": description,
                }
            )
            version_update_req.isValid()

            try:
                model = self.update_version(
                    org_name=org_name,
                    team_name=team_name,
                    model_name=mrt.name,
                    version=mrt.version,
                    version_update_request=version_update_req,
                    set_latest=set_latest,
                )
            except ResourceNotFoundException:
                raise ResourceNotFoundException(f"Model version '{target}' was not found.") from None

            return model

        self._validate_update_model(locals())

        labels_v2 = []
        if not mrt.version:
            if labels or label_set:
                labels_v2 = get_label_set_labels(self.client.registry.label_set, "MODEL", label_set, labels)
            else:
                labels_v2 = self.get(mrt.org or "", mrt.team or "", mrt.name or "").model.labels or []

        model_update_dict = {
            "application": application,
            "framework": framework,
            "modelFormat": model_format,
            "precision": precision,
            "shortDescription": short_description,
            "description": get_file_contents(overview_filename, "--overview-filename"),
            "displayName": display_name,
            "labelsV2": apply_labels_update(labels_v2, add_label or [], remove_label or []),
            "logo": logo,
            "publicDatasetUsed": handle_public_dataset_no_args(
                public_dataset_name=public_dataset_name,
                public_dataset_link=public_dataset_link,
                public_dataset_license=public_dataset_license,
            ),
            "builtBy": built_by,
            "publisher": publisher,
            "bias": get_file_contents(bias_filename, "--bias-filename"),
            "explainability": get_file_contents(explainability_filename, "--explainability-filename"),
            "privacy": get_file_contents(privacy_filename, "--privacy-filename"),
            "safetyAndSecurity": get_file_contents(safety_security_filename, "--safety-security-filename"),
        }
        model_update_request = ModelUpdateRequest(model_update_dict)
        model_update_request.isValid()
        try:
            resp = self.connection.make_api_request(
                "PATCH",
                self._get_models_endpoint(org=org_name, team=team_name, name=mrt.name),
                payload=model_update_request.toJSON(),
                auth_org=org_name,
                auth_team=team_name,
                operation_name="update model",
            )
        except ResourceNotFoundException:
            raise ResourceNotFoundException("Model '{}' was not found.".format(target)) from None
        return ModelResponse(resp).model

    @extra_args
    def create(  # noqa: D417
        self,
        target: str,
        application: str,
        framework: str,
        model_format: str,
        precision: str,
        short_description: str,
        overview_filename: Optional[str] = None,
        bias_filename: Optional[str] = None,
        explainability_filename: Optional[str] = None,
        privacy_filename: Optional[str] = None,
        safety_security_filename: Optional[str] = None,
        display_name: Optional[str] = None,
        label: List[Optional[str]] = None,
        label_set: List[Optional[str]] = None,
        logo: Optional[str] = None,
        public_dataset_name: Optional[str] = None,
        public_dataset_link: Optional[str] = None,
        public_dataset_license: Optional[str] = None,
        built_by: Optional[str] = None,
        publisher: Optional[str] = None,
        encryption_key_id: Optional[str] = None,
        encryption_key_description: Optional[str] = None,
    ) -> Model:
        """Create a Model.

        Args:
            target: Full name of model. org/[team/]name[:version]
            application: Application of model.
            framework: Framework of model.
            model_format: Format of model.
            precision: Precision of model.
            short_description: Short description of model.
            overview_filename: Overview filename of model. Defaults to None.
            bias_filename: Bias_filename of model. Defaults to None.
            explainability_filename: Explainability filename of model. Defaults to None.
            privacy_filename: Privacy filename of model. Defaults to None.
            safety_security_filename: Safety security filename of model. Defaults to None.
            display_name: Display name of model. Defaults to None.
            labels: Label of model. Defaults to None.
            label_sets: Label set of model. Defaults to None.
            logo: Logo of model. Defaults to None.
            public_dataset_name: Public dataset name of model. Defaults to None.
            public_dataset_link: Public dataset link of model. Defaults to None.
            public_dataset_license: Public dataset license of model. Defaults to None.
            built_by: Time of model built by. Defaults to None.
            publisher: Publisher of model. Defaults to None.
            encryption_key_id: ID of existing encryption key to use. \
                Must be scoped to the same org/team as the model. Defaults to None.
            encryption_key_description: Description for new encryption key to \
                create in the same org/team scope as the model. Defaults to None.

        Raises:
            ResourceAlreadyExistsException: If model already exists.

        Returns:
            Model: Created model object.
        """
        self.config.validate_configuration()
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_allowed=False)
        org_name = mrt.org
        team_name = mrt.team

        # Build encryption key structure
        encryption_key_dict = None
        if encryption_key_id:
            # Parse the encryption key ID to extract just the key name
            key_target = SimpleRegistryTarget(encryption_key_id, org_required=True, name_required=True)
            encryption_key_dict = {
                "useExistingKey": True,
                "encryptionKeyId": key_target.name,
            }
            assert (
                key_target.org == mrt.org and key_target.team == mrt.team
            ), "Encryption key scope must match model scope"
        elif encryption_key_description:
            encryption_key_dict = {
                "useExistingKey": False,
                "description": encryption_key_description,
            }

        model_create_dict = {
            # required
            "name": mrt.name,
            "application": application,
            "framework": framework,
            "modelFormat": model_format,
            "precision": precision,
            "shortDescription": short_description,
            # optional
            "description": get_file_contents(overview_filename, "--overview-filename"),
            "displayName": display_name,
            "labelsV2": get_label_set_labels(self.client.registry.label_set, "MODEL", label_set, label),
            "logo": logo,
            "publicDatasetUsed": handle_public_dataset_no_args(
                public_dataset_name=public_dataset_name,
                public_dataset_link=public_dataset_link,
                public_dataset_license=public_dataset_license,
            ),
            "builtBy": built_by,
            "publisher": publisher,
            "bias": get_file_contents(bias_filename, "--bias-filename"),
            "explainability": get_file_contents(explainability_filename, "--explainability-filename"),
            "privacy": get_file_contents(privacy_filename, "--privacy-filename"),
            "safetyAndSecurity": get_file_contents(safety_security_filename, "--safety-security-filename"),
        }

        # Add encryption key if specified
        if encryption_key_dict:
            model_create_dict["encryptionKey"] = encryption_key_dict

        model_create_request = ModelCreateRequest(model_create_dict)
        model_create_request.isValid()

        try:
            resp = self._create(org_name=org_name, team_name=team_name, mcr=model_create_request)
            if resp.model and resp.model.encryptionKeyId:
                resp.model.encryptionKeyId = (
                    f"{org_name}/{team_name}/{resp.model.encryptionKeyId}"
                    if team_name
                    else f"{org_name}/{resp.model.encryptionKeyId}"
                )
            return resp.model
        except ResourceAlreadyExistsException:
            raise ResourceAlreadyExistsException("Model '{}' already exists.".format(target)) from None

    @extra_args
    def info(
        self,
        target: str,
    ) -> Union[ModelResponse, ModelVersionResponse]:
        """Retrieve metadata for a model or model version.

        Args:
            target: Full model name. org/[team/]name[:version]

        Raises:
            ResourceNotFoundException: If model is not found.

        Returns:
            Union[ModelResponse, ModelVersionResponse]: model or model version depending on input
        """
        self.config.validate_configuration(guest_mode_allowed=True)
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True)

        if mrt.version:
            try:
                version_resp = self.get_version(
                    org_name=mrt.org, team_name=mrt.team, model_name=mrt.name, version=str(mrt.version)
                )
            except ResourceNotFoundException:
                raise ResourceNotFoundException("Target '{}' could not be found.".format(target)) from None
            return version_resp

        try:
            model_resp = self.get(mrt.org, mrt.team, mrt.name)
        except ResourceNotFoundException:
            raise ResourceNotFoundException("Target '{}' could not be found.".format(target)) from None
        return model_resp

    @extra_args
    def list(
        self,
        target: Optional[str] = None,
        org: Optional[str] = None,
        team: Optional[str] = None,
        order: Optional[str] = None,
        access_type: Optional[str] = None,
        product_names: Optional[str] = None,
        signed: bool = False,
        policy: Optional[List[str]] = None,
    ) -> Union[List[ModelVersion], List[RepositorySearchTransformer]]:
        """List model(s) or model version(s).

        Args:
            target: Name or pattern of models. Defaults to None.
            org: Organization. Defaults to None.
            team: Team. Defaults to None.
            order: Order by. Defaults to None.
            access_type: Access type filter of models. Defaults to None.
            product_names: Product type filter of models. Defaults to None.
            signed: Optional: If true, display models have signed version or versions that are signed, \
                depending on pattern.
            policy: Optional: Filter models based on policy labels.

        Raises:
            argparse.ArgumentTypeError: invalid input target

        Returns:
            Union[List[ModelVersion], List[RepositorySearchTransformer]]: \
                list of model version or list of models depending on input
        """
        self.config.validate_configuration(guest_mode_allowed=True, csv_allowed=True)
        mrt = ModelRegistryTarget(target, glob_allowed=True)
        _org, _team = get_auth_org_and_team(
            mrt.org, mrt.team, org or self.config.org_name, team or self.config.team_name
        )

        if mrt.version is None:
            if order:
                raise argparse.ArgumentTypeError(
                    "--sort argument is not valid for a model target, please specify a version."
                )
            return self.client.registry.search.search_model(
                _org, _team, target, access_type=access_type, product_names=product_names, signed=signed, policy=policy
            )

        if order is None:
            order = "SEMVER_DESC"
        try:
            version_list = self.list_versions(_org, _team, mrt.name, order=order)
        except ResourceNotFoundException:
            version_list = []
        version_list = filter_version_list(version_list, mrt.version, signed_only=signed, policy=policy)
        return version_list

    @extra_args
    def remove(self, target: str):
        """Remove model or model version.

        Args:
            target: Full model name. org/[team/]name[:version]

        Raises:
            ResourceNotFoundException: If model is not found.
        """
        self.config.validate_configuration()
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True)

        if mrt.version:
            try:
                self.remove_version(org_name=mrt.org, team_name=mrt.team, model_name=mrt.name, version=mrt.version)
            except ResourceNotFoundException:
                raise ResourceNotFoundException(f"Model version '{target}' could not be found.") from None
        else:
            try:
                self.remove_model(org_name=mrt.org, team_name=mrt.team, model_name=mrt.name)
            except ResourceNotFoundException:
                raise ResourceNotFoundException(f"Model '{target}' could not be found.") from None

    # END PUBLIC Functions

    @staticmethod
    def _get_models_endpoint(org: str = None, team: str = None, name: str = None) -> str:
        """Create a models endpoint.

        /v2[/org/<org>[/team/<team>[/<name>]]]/models
        """
        parts = [ENDPOINT_VERSION, format_org_team(org, team), "models", name]
        return "/".join([part for part in parts if part])

    def get_versions_endpoint(self, org: str = None, team: str = None, name: str = None, version: str = None) -> str:
        """Create a versions endpoint."""
        ep = self._get_models_endpoint(org=org, team=team, name=name)
        ep = "/".join([ep, "versions"])

        # version can be zero
        if version is not None:
            ep = "/".join([ep, str(version)])

        return ep

    def get_files_endpoint(
        self, org: str = None, team: str = None, name: str = None, version: str = None, file_: str = None
    ) -> str:
        """Create a files endpoint."""
        ep = self.get_versions_endpoint(org=org, team=team, name=name, version=version)
        ep = "/".join([ep, "files"])

        if file_:
            ep = "/".join([ep, str(file_)])

        return ep

    @staticmethod
    def get_multipart_files_endpoint(org: str = None, team: str = None) -> str:  # noqa: D102
        org_team = format_org_team(org, team)
        return f"{ENDPOINT_VERSION}/{org_team}/files/multipart"

    def get_direct_download_URL(  # noqa: D102
        self, name: str, version: str, org: str = None, team: str = None, filepath: str = None
    ) -> str:
        ep = f"{ENDPOINT_VERSION}/{format_org_team(org, team)}/models/{name}/{version}/files"
        if filepath:
            ep = f"{ep}?path={filepath}"
        return ep

    def get(self, org_name: str, team_name: str, model_name: str) -> ModelResponse:
        """Get a model."""
        params = {"resolve-labels": "false"}
        resp = self.connection.make_api_request(
            "GET",
            self._get_models_endpoint(org=org_name, team=team_name, name=model_name),
            auth_org=org_name,
            auth_team=team_name,
            params=params,
            operation_name="get model",
        )
        return ModelResponse(resp)

    def _create(self, org_name: str, team_name: str, mcr: ModelCreateRequest) -> ModelResponse:
        resp = self.connection.make_api_request(
            "POST",
            self._get_models_endpoint(org=org_name, team=team_name),
            payload=mcr.toJSON(),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="create model",
            timeout=CAS_TIMEOUT,
        )

        return ModelResponse(resp)

    def update_model(  # noqa: D102
        self, model_name: str, org_name: str, team_name: str, model_update_request: ModelUpdateRequest
    ):
        resp = self.connection.make_api_request(
            "PATCH",
            self._get_models_endpoint(org=org_name, team=team_name, name=model_name),
            payload=model_update_request.toJSON(),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="update model",
        )
        return ModelResponse(resp).model

    def _validate_update_version(self, args_dict):
        """Helper Function for update given a version is provided."""  # noqa: D401
        invalid_args = [arg[1] for arg in self.model_only_args if args_dict[arg[0]] is not None]
        if invalid_args:
            raise argparse.ArgumentTypeError(f"Invalid argument(s) for model version: '{invalid_args}'")
        if all(args_dict[arg[0]] is None for arg in self.version_only_args):
            raise argparse.ArgumentTypeError(
                "No arguments provided for model version update request, there is nothing to do."
            )

    def _validate_update_model(self, args_dict):
        """Helper Function for update given a version is not provided."""  # noqa: D401
        invalid_args = [f"{arg[1]}" for arg in self.version_only_args if args_dict[arg[0]] is not None]
        if invalid_args:
            raise argparse.ArgumentTypeError(f"Invalid argument(s): {invalid_args}.  Only valid for model-versions.")
        if all(args_dict[arg[0]] is None for arg in self.model_only_args):
            raise argparse.ArgumentTypeError("No arguments provided for model update, there is nothing to do.")

    def remove_model(self, org_name: str, team_name: str, model_name: str):
        """Remove a model."""
        self.connection.make_api_request(
            "DELETE",
            self._get_models_endpoint(org=org_name, team=team_name, name=model_name),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="remove model",
            timeout=CAS_TIMEOUT,
        )

    def list_versions(
        self, org_name: str, team_name: str, model_name: str, page_size: int = PAGE_SIZE, order: str = None
    ) -> Iterable[ModelVersion]:
        """Get a list of versions for a model."""
        base_url = self.get_versions_endpoint(org=org_name, team=team_name, name=model_name)
        params = dict({"page-size": page_size})
        if order:
            params["sort-order"] = order
        query = f"{base_url}?{urlencode(params)}"
        return chain(
            *[
                ModelVersionListResponse(res).modelVersions
                for res in pagination_helper_page_reference_iter_total_pages(
                    self.connection, query, org_name=org_name, team_name=team_name, operation_name="list model versions"
                )
                if ModelVersionListResponse(res).modelVersions
            ]
        )

    def get_version(self, org_name: str, team_name: str, model_name: str, version: str) -> ModelVersionResponse:
        """Get a model version."""
        resp = self.connection.make_api_request(
            "GET",
            self.get_versions_endpoint(org=org_name, team=team_name, name=model_name, version=version),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="get model version",
        )
        return ModelVersionResponse(resp)

    def create_version(
        self, org_name: str, team_name: str, model_name: str, version_create_request: ModelVersionCreateRequest
    ) -> ModelVersionResponse:
        """Create a model version."""
        resp = self.connection.make_api_request(
            "POST",
            self.get_versions_endpoint(org=org_name, team=team_name, name=model_name),
            payload=version_create_request.toJSON(),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="create model version",
        )
        return ModelVersionResponse(resp)

    def update_version(
        self,
        org_name: str,
        team_name: str,
        model_name: str,
        version: str,
        version_update_request: ModelVersionUpdateRequest,
        set_latest: bool = False,
    ) -> ModelVersionResponse:
        """Update a model version."""
        url = self.get_versions_endpoint(org=org_name, team=team_name, name=model_name, version=version)
        if set_latest:
            url += "?set-latest=true"

        resp = self.connection.make_api_request(
            "PATCH",
            url,
            payload=version_update_request.toJSON(),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="update model version",
        )
        return ModelVersionResponse(resp)

    def remove_version(self, org_name: str, team_name: str, model_name: str, version: str):
        """Remove a model version."""
        self.connection.make_api_request(
            "DELETE",
            self.get_versions_endpoint(org=org_name, team=team_name, name=model_name, version=version),
            auth_org=org_name,
            auth_team=team_name,
            operation_name="remove model version",
            timeout=CAS_TIMEOUT,
        )

    @extra_args
    def list_files(self, target: str, org: Optional[str] = None, team: Optional[str] = None):
        """Get a list of files for a model."""
        self.config.validate_configuration(guest_mode_allowed=True)
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True)
        if not mrt.version:
            raise InvalidArgumentError("Cannot list files for a model target; please specify a version")

        org_name = mrt.org or org or self.client.config.org_name
        team_name = mrt.team or team or self.client.config.team_name

        base_url = self.get_files_endpoint(org=org_name, team=team_name, name=mrt.name, version=mrt.version)
        query = f"{base_url}?{urlencode({'page-size': PAGE_SIZE})}"

        return chain(
            *[
                ModelVersionFileListResponse(res).modelFiles
                for res in pagination_helper_page_reference_iter_total_pages(
                    self.connection, query, org_name=org_name, team_name=team_name, operation_name="list model files"
                )
                if ModelVersionFileListResponse(res).modelFiles
            ]
        )

    def _get_latest_version(self, target):
        try:
            model_resp = self.get(target.org, target.team, target.name)
        except ResourceNotFoundException:
            raise ResourceNotFoundException("Target '{}' could not be found.".format(target)) from None
        latest_version = self._get_latest_version_from_artifact_response(model_resp)
        if not latest_version:
            raise NgcException("Target '{}' has no version available for download.".format(target))

        return latest_version

    def _update_upload_complete(self, org_name, team_name, model_name, version):
        version_req = ModelVersionUpdateRequest({"status": "UPLOAD_COMPLETE"})
        version_req.isValid()
        return self.update_version(org_name, team_name, model_name, version, version_req)

    def _stash_version(self, org, team, model, version):
        """Stash the version files, allow BE performs neccessary checks and update metadata.

        Call the end point '/org/{org-name}/models/{artifact-name}/versions/{version-id}/stash'.
        """
        ep = self.get_versions_endpoint(org, team, model, version) + "/stash"
        self.connection.make_api_request(
            "PATCH",
            ep,
            auth_org=org,
            auth_team=team,
            operation_name="stash model version",
        )

    # These lists are used for argument validate.
    model_only_args = [
        ("application", "--application"),
        ("framework", "--framework"),
        ("model_format", "--format"),
        ("precision", "--precision"),
        ("short_description", "--short-desc"),
        ("display_name", "--display-name"),
        ("bias_filename", "--bias-filename"),
        ("explainability_filename", "--explainability-filename"),
        ("privacy_filename", "--privacy-filename"),
        ("safety_security_filename", "--safety-security-filename"),
        ("labels", "--label"),
        ("add_label", "--add-label"),
        ("remove_label", "--remove-label"),
        ("logo", "--logo"),
        ("public_dataset_name", "--public-dataset-name"),
        ("public_dataset_link", "--public-dataset-link"),
        ("public_dataset_license", "--public-dataset-license"),
        ("built_by", "--built-by"),
        ("overview_filename", "--overview-filename"),
        ("publisher", "--publisher"),
        ("label_set", "--label-set"),
    ]
    version_only_args = [
        ("gpu_model", "--gpu-model"),
        ("memory_footprint", "--memory-footprint"),
        ("num_epochs", "--num-epochs"),
        ("batch_size", "--batch-size"),
        ("accuracy_reached", "--accuracy-reached"),
        ("description", "--description"),
        ("set_latest", "--set-latest"),
    ]

    @extra_args
    def publish(
        self,
        target,
        source: Optional[str] = None,
        metadata_only=False,
        version_only=False,
        visibility_only=False,
        allow_guest=False,
        discoverable=False,
        public=False,
        access_type: Optional[str] = None,
        product_names: Optional[List[str]] = None,
        upload_pending=False,
        license_terms_specs: Optional[List[LicenseMetadata]] = None,
        sign=False,
        nspect_id: Optional[str] = None,
        policy: Optional[List[str]] = None,
    ):
        """Publishes a model with various options for metadata, versioning, and visibility.

        This method manages the publication of models to a repository, handling
        different aspects of the publication such as metadata only, version only, and
        visibility adjustments. It validates the combination of arguments provided
        and processes the publication accordingly.
        There are two seperate publishing flows in the follow precedence:
            unified catalog publishing: sets the product names and access type of the model.
            legacy publishing: sets the discoverable, public, allow_guest of the model.
        """  # noqa: D401
        self.config.validate_configuration(guest_mode_allowed=False)
        if not metadata_only and source:
            _source = ModelRegistryTarget(source, org_required=True, name_required=True)
            if _source.version is None:
                _version = self._get_latest_version(_source)
                logger.info("No version specified for %s, using version: %s", source, _version)
                source += f":{_version}" if _version else ""

        return self.client.registry.publish.publish(
            self.resource_type,
            self.config.org_name,
            self.config.team_name,
            target,
            source,
            metadata_only,
            version_only,
            visibility_only,
            allow_guest,
            discoverable,
            public,
            sign,
            access_type,
            product_names,
            upload_pending,
            license_terms_specs,
            nspect_id,
            # resource artifact publishing uses this publish function, not neccessarily defined callback
            validation_callback=self.publish_validation_callback,
            policy=policy,
        )

    def update_license_terms(self, target: str, license_terms_specs: Optional[List[LicenseMetadata]] = None):
        """Update a model's license terms of services.

        Args:
            target: Full model name. Format: org/[team/]name.
            license_terms_specs: License terms to.
        """
        self.config.validate_configuration(guest_mode_allowed=False)
        return self.client.registry.publish.update_license_terms(
            self.resource_type,
            target,
            self.config.org_name,
            self.config.team_name,
            license_terms_specs,
        )

    def sign(self, target: str):
        """Request model version to get signed.

        Args:
            target: Full model name. Format: org/[team/]name:version.

        Raises:
            ArgumentTypeError: If the target is invalid.
        """
        self.config.validate_configuration(guest_mode_allowed=False)
        model = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=True)
        url = self.get_versions_endpoint(org=model.org, team=model.team, name=model.name, version=model.version)
        url += "/signature"
        self.connection.make_api_request(
            "PUT",
            url,
            auth_org=self.config.org_name,
            auth_team=self.config.team_name,
            operation_name=f"request version signature for {target}",
        )

    # PUBLIC FUNCTIONS
    @extra_args
    def download_version_signature(
        self,
        target: str,
        destination: Optional[str] = ".",
        dry_run: Optional[bool] = False,
    ) -> None:
        """Download the signature of specified model version.

        Args:
            target: Full model name. org/[team/]name[:version]
            destination: Where to save the file. Defaults to ".".
            dry_run: If True, will not download the signature file.

        Raises:
            NgcException: If unable to download.
            ResourceNotFoundException: If model is not found.

        """
        self.config.validate_configuration(guest_mode_allowed=True)
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=False)

        if not mrt.version:
            mrt.version = self._get_latest_version(mrt)
            target += f":{mrt.version}"
            self.transfer_printer.print_ok(f"No version specified, downloading latest version: '{mrt.version}'.")

        try:
            version_resp = self.get_version(mrt.org, mrt.team, mrt.name, mrt.version)
            if not self._get_version_from_response(version_resp).isSigned:
                raise NgcException(f"'{target}' is not signed.")
        except ResourceNotFoundException:
            raise ResourceNotFoundException(f"'{target}' could not be found.") from None

        # Query for presigned download URL
        self.transfer_printer.print_download_message("Getting file to download...\n")
        ep = self.get_versions_endpoint(org=mrt.org, team=mrt.team, name=mrt.name, version=mrt.version)
        url = "/".join([ep, "signature"])
        resp = self.connection.make_api_request(
            "GET",
            url,
            auth_org=self.config.org_name,
            auth_team=self.config.team_name,
            operation_name=f"get signature download url for {target}",
        )
        presigned_url = resp["url"]

        # Download the signature file
        if not dry_run:
            with TracedSession() as session:
                file_content_resp = session.get(
                    use_noncanonical_url(presigned_url),
                    operation_name="download model signature",
                )
            file_content_resp.raise_for_status()
            outfile = validate_destination(destination, mrt, "result.sigstore", create=True)
            with open(outfile, "wb") as ff:
                ff.write(file_content_resp.content)
            self.transfer_printer.print_single_file_download_status("COMPLETED", outfile)

    def get_public_key(self, destination: Optional[str] = "."):
        """Download the public key used to sign models.

        Args:
            destination: Where to save the file. Defaults to '.'
        """
        self.config.validate_configuration(guest_mode_allowed=True)
        self.client.registry.publish.get_public_key(self.resource_type, destination)

    def _get_version_from_response(self, response: ModelVersionResponse):  # noqa: R0201 pylint: disable=no-self-use
        return response.modelVersion

    def _get_model_from_response(self, response: ModelResponse):  # noqa: R0201 pylint: disable=no-self-use
        return response.model

    def _get_latest_version_from_artifact_response(
        self, response: ModelResponse
    ):  # noqa: R0201 pylint: disable=no-self-use
        return response.model.latestVersionIdStr

    def _get_status_from_version_response(
        self, response: ModelVersionResponse
    ):  # noqa: R0201 pylint: disable=no-self-use
        return response.modelVersion.status

    def validate_base_version(self, org: str, team: str, name: str, base_version: str):
        """Validate base_version argument."""
        if ":" in base_version:
            raise NgcException(
                "Base version should only include version ID, should not include org, team or artifact name."
            )
        _name = "/".join(i for i in [org, team, name] if i) + f":{base_version}"
        try:
            version_resp = self.get_version(org, team, name, base_version)
            version_obj = self._get_version_from_response(version_resp)
        except ResourceNotFoundException:
            raise NgcException(f"Base version {_name} cannot found.") from None

        if version_obj.totalFileCount == 0:
            raise NgcException(f"Base version {_name} contains no files, it cannot be used as a base version.")
        if version_obj.storageVersion != "V2":
            raise NgcException(
                f"Base version {_name} was created with legacy upload scheme, it cannot be used as a base version."
            )
        if version_obj.status != "UPLOAD_COMPLETE":
            raise NgcException(
                f"Base version {_name} is in the {version_obj.status} state, cannot be used as a base version."
            )

    def validated_storage_version(
        self, mrt: ModelRegistryTarget, create_request, base_version: Optional[str] = None
    ) -> Literal["V1", "V2"]:
        """Validate storage versions before the upload.

        target version:

                    upload_pending            |      upload_complete
        v1        base_version not allowed    |        not allowed
        v2        base_version allowed        |        not allowed

        base_version:

            upload_pending  |  upload_complete
        v1   not allowed      |   not allowed
        v2   not allowed      |   allowed
        """
        if base_version:
            self.validate_base_version(mrt.org, mrt.team, mrt.name, base_version)

        try:
            version_response = self.create_version(mrt.org, mrt.team, mrt.name, create_request)
        except ResourceAlreadyExistsException:
            version_response = self.get_version(mrt.org, mrt.team, mrt.name, mrt.version)

        version_object = self._get_version_from_response(version_response)
        if version_object.status == "UPLOAD_COMPLETE":
            raise ResourceAlreadyExistsException("Target '{}' already exists.".format(mrt))

        storage_version = version_object.storageVersion
        if storage_version == "V1":
            if base_version:
                raise NgcException(
                    f"{self.resource_type.title()} {mrt} was created with legacy upload "
                    "scheme(v1 storage version), base version is not supported."
                )
            return storage_version

        return "V2"

    def publish_validation_callback(self, **kwargs):
        """Perform validation after forming publish request.

        This is a callback function for the common publish function.
        This validates that the source resource is in UPLOAD_COMPLETE state when
        publishing version.
        """
        if not kwargs.get("metadata_only") and not kwargs.get("visibility_only") and kwargs.get("source"):
            _s = kwargs["source"]
            mrt = ModelRegistryTarget(_s)
            if mrt.version:
                version_response = self.get_version(mrt.org, mrt.team, mrt.name, mrt.version)
                _state = self._get_status_from_version_response(version_response)
                if _state != "UPLOAD_COMPLETE":
                    raise NgcException(
                        "Publishing target to the UPLOAD_PENDING status "
                        f"must have the source in UPLOAD_COMPLETE state, currently [{_state}]. "
                        f"Please commit the source."
                    )


class GuestModelAPI(ModelAPI):  # noqa: D101
    @staticmethod
    def _get_models_endpoint(org: str = None, team: str = None, name: str = None):
        """Create a guest models endpoint.
        /{ENDPOINT_VERSION}/models[/<org>[/<team>[/<name>]]]
        """  # noqa: D205, D415
        ep = f"{ENDPOINT_VERSION}/models"
        if org:
            ep = "/".join([ep, org])
        if team:
            ep = "/".join([ep, team])
        if name:
            ep = "/".join([ep, name])
        return ep

    def get_direct_download_URL(  # noqa: D102
        self, name: str, version: str, org: str = None, team: str = None, filepath: str = None
    ):
        org_team = format_org_team(org, team)
        ep = "/".join([item for item in (ENDPOINT_VERSION, "models", org_team, name, version, "files") if item])
        if filepath:
            ep = f"{ep}?path={filepath}"
        return ep

    def _get_license_terms(self, target):
        """Get license terms for a model."""
        mrt = ModelRegistryTarget(target, org_required=True, name_required=True, version_required=False)
        resp = self.get(mrt.org, mrt.team, mrt.name)
        return resp.model.licenseTerms

    def download_version(
        self,
        target,
        destination=".",
        file_patterns=None,
        exclude_patterns=None,
        progress_callback_func: Optional[Callable[[int, int, int, int, int, int], None]] = None,
        agree_license=False,
    ):
        """Download the specified model version to a local directory.

        Args:
            target: Full model name. org/[team/]name[:version]
            destination: Description of model. Defaults to ".".
            file_patterns: Inclusive filter of model files. Defaults to None.
            exclude_patterns: Exclusive filter of model files. Defaults to None.
            progress_callback_func (Optional[Callable[[int, int, int, int, int, int], None]]):
                A callback function that accepts six integers representing
                completed_bytes, failed_bytes, total_bytes, completed_count,
                failed_count, and total_count respectively. If provided,
                this function will be called to report progress periodically.
                If set to None, progress updates will not be reported.
            agree_license (bool, False): Must be set to True if to accept license to omit warning.

        Returns:
            DotDict: A dictionary-like object with attribute access, containing the following fields:
            - `transfer_id` (str): Unique identifier for the transfer session.
            - `status` (str): Final status of the transfer (e.g., "completed", "failed").
            - `path` (str): Local path to the directory where the data was downloaded to.
            - `duration_seconds` (float): Total duration of the transfer in seconds.
            - `completed_count` (int): Number of files successfully transferred.
            - `completed_bytes` (int): Total number of bytes successfully transferred.
            - `started_at` (str): ISO 8601 timestamp when the transfer began.
            - `ended_at` (str): ISO 8601 timestamp when the transfer ended.

        Raises:
            ResourceNotFoundException: If the specified model could not be found.
            RuntimeError: If the model requires license acceptance but `agree_license` is not set to True.
        """
        # Perform license check for guest downloads
        self.client.registry.publish.check_license_for_guest_download(self, target, agree_license)

        return super().download_version(target, destination, file_patterns, exclude_patterns, progress_callback_func)
