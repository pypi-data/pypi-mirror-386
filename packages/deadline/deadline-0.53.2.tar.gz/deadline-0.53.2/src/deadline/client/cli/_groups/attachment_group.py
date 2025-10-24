# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
All the `deadline attachment` commands:
    * upload
    * download
"""

from __future__ import annotations

import click
import boto3
from dataclasses import asdict
from typing import Optional

from .click_logger import ClickLogger
from .._common import _apply_cli_options_to_config, _handle_error
from ...config import config_file
from .._main import main

from deadline.client import api
from deadline.job_attachments.api.attachment import (
    _attachment_download,
    _attachment_upload,
)
from deadline.job_attachments._aws.deadline import get_queue
from deadline.job_attachments.exceptions import MissingJobAttachmentSettingsError
from deadline.job_attachments.models import FileConflictResolution, JobAttachmentS3Settings
from deadline.job_attachments.progress_tracker import DownloadSummaryStatistics


@main.group(name="attachment")
@_handle_error
def cli_attachment():
    """
    Commands to work with Deadline Cloud Job Attachments.
    """


@cli_attachment.command(
    name="download",
    help="BETA - Download Job Attachment data files for given manifest(s).",
)
@click.option(
    "-m",
    "--manifests",
    multiple=True,
    required=True,
    help="File path(s) to manifest formatted file(s). File name has to contain the hash of corresponding source path.",
)
@click.option(
    "--s3-root-uri", help="Job Attachments S3 root uri including bucket name and root prefix."
)
@click.option("--path-mapping-rules", help="Path to a file with the path mapping rules to use.")
@click.option("--farm-id", help="The AWS Deadline Cloud Farm to use. ")
@click.option("--queue-id", help="The AWS Deadline Cloud Queue to use. ")
@click.option(
    "--profile", help="The AWS profile to use for interacting with Job Attachments S3 bucket."
)
@click.option(
    "--conflict-resolution",
    type=click.Choice(
        [
            FileConflictResolution.SKIP.name,
            FileConflictResolution.OVERWRITE.name,
            FileConflictResolution.CREATE_COPY.name,
        ],
        case_sensitive=False,
    ),
    help="How to handle downloads if a file already exists:\n"
    "CREATE_COPY (default): Download the file with a new name, appending '(X)' to the end. X is incremented for each duplicate\n"
    "SKIP: Do not download the file\n"
    "OVERWRITE: Download and replace the existing file",
)
@click.option("--json", default=None, is_flag=True, help="Output is printed as JSON for scripting.")
@_handle_error
def attachment_download(
    manifests: list[str],
    s3_root_uri: str,
    path_mapping_rules: str,
    json: bool,
    **args,
):
    """
    Download data files of manifest root(s) to a machine for given manifest(s) from S3.
    """
    logger: ClickLogger = ClickLogger(is_json=json)

    # Setup config
    config = _apply_cli_options_to_config(**args)

    # Assuming when passing with config, session constructs from the profile id for S3 calls
    # TODO - add type for profile, if queue type, get queue session directly
    boto3_session: boto3.session = api.get_boto3_session(config=config)

    # If profile is not provided via args, default to use local config file
    if not args.pop("profile", None):
        queue_id: str = config_file.get_setting("defaults.queue_id", config=config)
        farm_id: str = config_file.get_setting("defaults.farm_id", config=config)

        s3_settings: Optional[JobAttachmentS3Settings] = get_queue(
            farm_id=farm_id,
            queue_id=queue_id,
            session=boto3_session,
        ).jobAttachmentSettings
        if not s3_settings:
            raise MissingJobAttachmentSettingsError(f"Queue {queue_id} has no attachment settings")

        s3_root_uri = s3_settings.to_s3_root_uri()

        deadline_client = boto3_session.client("deadline")
        boto3_session = api.get_queue_user_boto3_session(deadline=deadline_client, config=config)

    if not s3_root_uri:
        raise MissingJobAttachmentSettingsError("No valid s3 root path available")

    # Apply conflict resolution setting from Config.
    conflict_resolution = FileConflictResolution.CREATE_COPY
    conflict_resolution_setting = config_file.get_setting(
        "settings.conflict_resolution", config=config
    )
    if (
        conflict_resolution_setting
        and conflict_resolution_setting != FileConflictResolution.NOT_SELECTED.name
    ):
        conflict_resolution = FileConflictResolution[conflict_resolution_setting]

    download_summary: DownloadSummaryStatistics = _attachment_download(
        manifests=manifests,
        s3_root_uri=s3_root_uri,
        boto3_session=boto3_session,
        path_mapping_rules=path_mapping_rules,
        print_function_callback=logger.echo,
        conflict_resolution=conflict_resolution,
    )

    logger.echo(download_summary)
    logger.json(asdict(download_summary.convert_to_summary_statistics()))


@cli_attachment.command(
    name="upload",
    help="BETA - Upload Job Attachment data files for given manifest(s).",
)
@click.option(
    "-m",
    "--manifests",
    multiple=True,
    required=True,
    help="File path(s) to manifest formatted file(s). File name has to contain the hash of corresponding source path.",
)
@click.option(
    "-r",
    "--root-dirs",
    multiple=True,
    help="The root directory of assets to upload.",
)
@click.option("--path-mapping-rules", help="Path to a file with the path mapping rules to use.")
@click.option(
    "--s3-root-uri", help="Job Attachments S3 root uri including bucket name and root prefix."
)
@click.option(
    "--upload-manifest-path", default=None, help="File path for uploading the manifests to CAS."
)
@click.option("--farm-id", help="The AWS Deadline Cloud Farm to use. ")
@click.option("--queue-id", help="The AWS Deadline Cloud Queue to use. ")
@click.option(
    "--profile", help="The AWS profile to use for interacting with Job Attachments S3 bucket."
)
@click.option("--json", default=None, is_flag=True, help="Output is printed as JSON for scripting")
@_handle_error
def attachment_upload(
    manifests: list[str],
    root_dirs: list[str],
    path_mapping_rules: str,
    s3_root_uri: str,
    upload_manifest_path: str,
    json: bool,
    **args,
):
    """
    Upload output files to s3. The files always include data files, optionally upload manifests prefixed by given path.
    """
    logger: ClickLogger = ClickLogger(is_json=json)

    # Setup config
    config = _apply_cli_options_to_config(**args)

    # Assuming when passing with config, session constructs from the profile id for S3 calls
    # TODO - add type for profile, if queue type, get queue session directly
    boto3_session: boto3.session = api.get_boto3_session(config=config)

    # If profile is not provided via args, default to use local config file
    if not args.pop("profile", None):
        queue_id: str = config_file.get_setting("defaults.queue_id", config=config)
        farm_id: str = config_file.get_setting("defaults.farm_id", config=config)

        s3_settings: Optional[JobAttachmentS3Settings] = get_queue(
            farm_id=farm_id,
            queue_id=queue_id,
            session=boto3_session,
        ).jobAttachmentSettings
        if not s3_settings:
            raise MissingJobAttachmentSettingsError(f"Queue {queue_id} has no attachment settings")

        s3_root_uri = s3_settings.to_s3_root_uri()

        deadline_client = boto3_session.client("deadline")
        boto3_session = api.get_queue_user_boto3_session(deadline=deadline_client, config=config)

    if not s3_root_uri:
        raise MissingJobAttachmentSettingsError("No valid s3 root path available")

    _attachment_upload(
        root_dirs=root_dirs,
        manifests=manifests,
        s3_root_uri=s3_root_uri,
        boto3_session=boto3_session,
        path_mapping_rules=path_mapping_rules,
        upload_manifest_path=upload_manifest_path,
        print_function_callback=logger.echo,
    )
