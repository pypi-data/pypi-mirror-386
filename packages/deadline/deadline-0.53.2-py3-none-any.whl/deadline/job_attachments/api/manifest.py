# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import datetime
from io import BytesIO
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import boto3

from deadline.client.api._session import _get_queue_user_boto3_session, get_default_client_config
from deadline.job_attachments._diff import _fast_file_list_to_manifest_diff, compare_manifest
from deadline.job_attachments._glob import _process_glob_inputs, _glob_paths
from deadline.job_attachments.api._utils import _read_manifests
from deadline.job_attachments.asset_manifests._create_manifest import (
    _create_manifest_for_single_root,
)
from deadline.job_attachments.asset_manifests.base_manifest import (
    BaseAssetManifest,
    BaseManifestPath,
)
from deadline.client.config import config_file
from deadline.job_attachments.asset_manifests.decode import decode_manifest
from deadline.job_attachments.asset_manifests.hash_algorithms import hash_data
from deadline.job_attachments.caches.hash_cache import HashCache
from deadline.job_attachments.download import (
    get_manifest_from_s3,
    get_output_manifests_by_asset_root,
    merge_asset_manifests,
)
from deadline.job_attachments.models import (
    S3_MANIFEST_FOLDER_NAME,
    FileStatus,
    GlobConfig,
    JobAttachmentS3Settings,
    ManifestDiff,
    ManifestDownload,
    ManifestDownloadResponse,
    ManifestSnapshot,
    ManifestMerge,
    default_glob_all,
    AssetType,
)
from deadline.job_attachments._utils import _get_long_path_compatible_path
from deadline.job_attachments.upload import S3AssetManager, S3AssetUploader

"""
APIs here should be business logic only. It should perform one thing, and one thing well. 
It should use basic primitives like S3 upload, download, boto3 APIs.
These APIs should be boto3 session agnostic and a specific Boto3 Credential to use.
"""


def _glob_files(
    root: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    include_exclude_config: Optional[str] = None,
) -> List[str]:
    """
    :param include: Include glob to look for files to add to the manifest.
    :param exclude: Exclude glob to exclude files from the manifest.
    :param include_exclude_config: Config JSON or file containeing input and exclude config.
    :returns: All files matching the include and exclude expressions.
    """

    # Get all files in the root.
    glob_config: GlobConfig
    if include or exclude:
        include = include if include is not None else default_glob_all()
        exclude = exclude if exclude is not None else []
        glob_config = GlobConfig(include_glob=include, exclude_glob=exclude)
    elif include_exclude_config:
        glob_config = _process_glob_inputs(include_exclude_config)
    else:
        # Default, include all.
        glob_config = GlobConfig()

    input_files = _glob_paths(
        root, include=glob_config.include_glob, exclude=glob_config.exclude_glob
    )
    return input_files


def _manifest_snapshot(
    root: str,
    destination: str,
    name: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    include_exclude_config: Optional[str] = None,
    diff: Optional[str] = None,
    force_rehash: bool = False,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> Optional[ManifestSnapshot]:
    # Get all files in the root.
    glob_config: GlobConfig
    if include or exclude:
        include = include if include is not None else default_glob_all()
        exclude = exclude if exclude is not None else []
        glob_config = GlobConfig(include_glob=include, exclude_glob=exclude)
    elif include_exclude_config:
        glob_config = _process_glob_inputs(include_exclude_config)
    else:
        # Default, include all.
        glob_config = GlobConfig()

    current_files = _glob_paths(
        root, include=glob_config.include_glob, exclude=glob_config.exclude_glob
    )

    # Compute the output manifest immediately and hash.
    if not diff:
        output_manifest = _create_manifest_for_single_root(
            files=current_files, root=root, print_function_callback=print_function_callback
        )
        if not output_manifest:
            return None

    # If this is a diff manifest, load the supplied manifest file.
    else:
        # Parse local manifest
        with open(diff) as source_diff:
            source_manifest_str = source_diff.read()
            source_manifest = decode_manifest(source_manifest_str)

        # Get the differences
        changed_paths: List[str] = []

        # Fast comparison using time stamps and sizes.
        if not force_rehash:
            diff_list: List[Tuple[str, FileStatus]] = _fast_file_list_to_manifest_diff(
                root=root,
                current_files=current_files,
                diff_manifest=source_manifest,
                print_function_callback=print_function_callback,
                return_root_relative_path=False,
            )
            for diff_file in diff_list:
                # Add all new and modified
                if diff_file[1] != FileStatus.DELETED:
                    changed_paths.append(diff_file[0])
        else:
            # In "slow / thorough" mode, we check by hash, which is definitive.
            output_manifest = _create_manifest_for_single_root(
                files=current_files, root=root, print_function_callback=print_function_callback
            )
            if not output_manifest:
                return None
            differences: List[Tuple[FileStatus, BaseManifestPath]] = compare_manifest(
                source_manifest, output_manifest
            )
            for diff_item in differences:
                if diff_item[0] == FileStatus.MODIFIED or diff_item[0] == FileStatus.NEW:
                    full_diff_path = f"{root}/{diff_item[1].path}"
                    changed_paths.append(full_diff_path)
                    print_function_callback(
                        f"Found difference at: {full_diff_path}, Status: {diff_item[0]}"
                    )

        # If there were no files diffed, return None, there was nothing to snapshot.
        if len(changed_paths) == 0:
            return None

        # Since the files are already hashed, we can easily re-use has_attachments to remake a diff manifest.
        output_manifest = _create_manifest_for_single_root(
            files=changed_paths, root=root, print_function_callback=print_function_callback
        )
        if not output_manifest:
            return None

    # Write created manifest into local file, at the specified location at destination
    if output_manifest is not None:
        local_manifest_file = _write_manifest(
            root=root,
            manifest=output_manifest,
            destination=destination,
            name=name,
        )
        # Output results.
        print_function_callback(f"Manifest generated at {local_manifest_file}")
        return ManifestSnapshot(root=root, manifest=local_manifest_file)
    else:
        # No manifest generated.
        print_function_callback("No manifest generated")
        return None


def _write_manifest(
    root: str,
    manifest: BaseAssetManifest,
    destination: str,
    name: Optional[str] = None,
) -> str:
    """
    Write a manifest to a destination.
    """
    # Write created manifest into local file, at the specified location at destination
    root_hash: str = hash_data(root.encode("utf-8"), manifest.get_default_hash_alg())
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    manifest_name = name if name else root.replace("/", "_").replace("\\", "_").replace(":", "_")
    manifest_name = manifest_name[1:] if manifest_name[0] == "_" else manifest_name
    manifest_name = f"{manifest_name}-{root_hash}-{timestamp}.manifest"

    local_manifest_path = str(
        _get_long_path_compatible_path(
            os.path.join(destination, manifest_name),
        )
    )
    os.makedirs(os.path.dirname(local_manifest_path), exist_ok=True)
    with open(local_manifest_path, "w") as file:
        file.write(manifest.encode())

    return local_manifest_path


def _manifest_diff(
    manifest: str,
    root: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    include_exclude_config: Optional[str] = None,
    force_rehash=False,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> ManifestDiff:
    """
    BETA API - This API is still evolving but will be made public in the near future.
    API to diff a manifest root with a previously snapshotted manifest.
    :param manifest: Manifest file path to compare against.
    :param root: Root directory to generate the manifest fileset.
    :param include: Include glob to look for files to add to the manifest.
    :param exclude: Exclude glob to exclude files from the manifest.
    :param include_exclude_config: Config JSON or file containeing input and exclude config.
    :param print_function_callback: Callback function to handle print messages.
    :returns: ManifestDiff object containing all new changed, deleted files.
    """

    # Find all files matching our regex
    input_files = _glob_files(
        root=root, include=include, exclude=exclude, include_exclude_config=include_exclude_config
    )
    input_paths = [Path(p) for p in input_files]

    # Placeholder Asset Manager
    asset_manager = S3AssetManager()

    # parse the given manifest to compare against.
    local_manifest_object: BaseAssetManifest
    with open(manifest) as input_file:
        manifest_data_str = input_file.read()
        local_manifest_object = decode_manifest(manifest_data_str)

    output: ManifestDiff = ManifestDiff()

    # Helper function to update output datastructure.
    def process_output(status: FileStatus, path: str, output_diff: ManifestDiff):
        if status == FileStatus.MODIFIED:
            output_diff.modified.append(path)
        elif status == FileStatus.NEW:
            output_diff.new.append(path)
        elif status == FileStatus.DELETED:
            output_diff.deleted.append(path)

    if force_rehash:
        # hash and create manifest of local directory
        cache_config = config_file.get_cache_directory()
        with HashCache(cache_config) as hash_cache:
            directory_manifest_object = asset_manager._create_manifest_file(
                input_paths=input_paths, root_path=root, hash_cache=hash_cache
            )

        # Hash based compare manifests.
        differences: List[Tuple[FileStatus, BaseManifestPath]] = compare_manifest(
            reference_manifest=local_manifest_object, compare_manifest=directory_manifest_object
        )
        # Map to output datastructure.
        for item in differences:
            process_output(item[0], item[1].path, output)

    else:
        # File based comparisons.
        fast_diff: List[Tuple[str, FileStatus]] = _fast_file_list_to_manifest_diff(
            root=root,
            current_files=input_files,
            diff_manifest=local_manifest_object,
            print_function_callback=print_function_callback,
        )
        for fast_diff_item in fast_diff:
            process_output(fast_diff_item[1], fast_diff_item[0], output)

    return output


def _manifest_upload(
    manifest_file: str,
    s3_bucket_name: str,
    s3_cas_prefix: str,
    boto_session: boto3.Session,
    s3_key_prefix: Optional[str] = None,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
):
    """
    BETA API - This API is still evolving but will be made public in the near future.
    API to upload a job attachment manifest to the Content Addressable Storage. Manifests will be
    uploaded to s3://{s3_bucket_name}/{cas_prefix}/Manifests/{s3_key_prefix}/{manifest_file_name} as per the Deadline CAS folder structure.
    manifest_file: File Path to the manifest file for upload.
    s3_bucket_name: S3 bucket name.
    boto_session: S3 Content Addressable Storage prefix.
    s3_key_prefix: [Optional] S3 prefix path to the Content Addressable Storge.
    boto_session: Boto3 session.
    print_function_callback: Callback function to handle print messages.
    """
    # S3 metadata

    # Upload settings:
    s3_metadata: Dict[str, Any] = {"Metadata": {}}
    s3_metadata["Metadata"]["file-system-location-name"] = manifest_file

    # Always upload the manifest file to case root /Manifest with the original file name.
    manifest_path: str = "/".join(
        [s3_cas_prefix, S3_MANIFEST_FOLDER_NAME, s3_key_prefix, Path(manifest_file).name]
        if s3_key_prefix
        else [s3_cas_prefix, S3_MANIFEST_FOLDER_NAME, Path(manifest_file).name]
    )

    # S3 uploader.
    upload = S3AssetUploader(session=boto_session)

    manifest_file = str(_get_long_path_compatible_path(manifest_file))

    with open(manifest_file) as manifest:
        upload.upload_bytes_to_s3(
            bytes=BytesIO(manifest.read().encode("utf-8")),
            bucket=s3_bucket_name,
            key=manifest_path,
            progress_handler=print_function_callback,
            extra_args=s3_metadata,
        )


def _manifest_download(
    download_dir: str,
    farm_id: str,
    queue_id: str,
    job_id: str,
    boto3_session: boto3.Session,
    step_id: Optional[str] = None,
    asset_type: AssetType = AssetType.ALL,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> ManifestDownloadResponse:
    """
    BETA API - This API is still evolving but will be made public in the near future.
    API to download the Job Attachment manifest for a Job, and optionally dependencies for Step.
    download_dir: Download directory.
    farm_id: The Deadline Farm to download from.
    queue_id: The Deadline Queue to download from.
    job_id: Job Id to download.
    boto_session: Boto3 session.
    step_id: Optional[str]: Optional, download manifest for a step
    asset_type: Which asset manifests should be downloaded for given job (& optionally step), options are Input, Output, All. Default behaviour is All.
    print_function_callback: Callback function to handle print messages.
    return ManifestDownloadResponse Downloaded Manifest data. Contains source S3 key and local download path.
    """

    # Deadline Client and get the Queue to download.
    deadline = boto3_session.client("deadline", config=get_default_client_config())

    queue: dict = deadline.get_queue(
        farmId=farm_id,
        queueId=queue_id,
    )

    # assume queue role - session permissions
    queue_role_session: boto3.Session = _get_queue_user_boto3_session(
        deadline=deadline,
        base_session=boto3_session,
        farm_id=farm_id,
        queue_id=queue_id,
        queue_display_name=queue["displayName"],
    )

    # Queue's Job Attachment settings.
    queue_s3_settings = JobAttachmentS3Settings(**queue["jobAttachmentSettings"])

    # Get S3 prefix
    s3_prefix: Path = Path(queue_s3_settings.rootPrefix, S3_MANIFEST_FOLDER_NAME)

    # Capture a list of success download files for JSON output.
    successful_downloads: List[ManifestDownload] = []

    # Utility function to build up manifests by root.
    manifests_by_root: Dict[str, List[BaseAssetManifest]] = dict()

    # Set the values of download input & output as per selected asset types in the api request
    download_input: bool = (
        True if asset_type is None or asset_type in (AssetType.INPUT, AssetType.ALL) else False
    )
    download_output: bool = (
        True if asset_type is None or asset_type in (AssetType.OUTPUT, AssetType.ALL) else False
    )

    def add_manifest_by_root(
        manifests_by_root: Dict[str, list], root: str, manifest: BaseAssetManifest
    ):
        if root not in manifests_by_root:
            manifests_by_root[root] = []
        manifests_by_root[root].append(manifest)

    # Get the job from deadline api
    job: dict = deadline.get_job(farmId=farm_id, queueId=queue_id, jobId=job_id)

    # If input manifests need to be downloaded
    if download_input:
        print_function_callback(f"Downloading input manifests for job: {job_id}")

        # Get input_manifest_paths from Deadline GetJob API
        attachments: dict = job.get("attachments", {})
        input_manifest_paths: List[Tuple[str, str]] = [
            (manifest.get("inputManifestPath", ""), manifest["rootPath"])
            for manifest in attachments.get("manifests", [])
        ]

        # Download each input_manifest_path
        for input_manifest_path, root_path in input_manifest_paths:
            asset_manifest: BaseAssetManifest = get_manifest_from_s3(
                manifest_key=(s3_prefix / input_manifest_path).as_posix(),
                s3_bucket=queue_s3_settings.s3BucketName,
                session=queue_role_session,
            )
            if asset_manifest is not None:
                print_function_callback(f"Found input manifest for root: {root_path}")
                add_manifest_by_root(
                    manifests_by_root=manifests_by_root, root=root_path, manifest=asset_manifest
                )

        # Now handle step-step dependencies
        if step_id is not None:
            print_function_callback(f"Finding step-step dependency manifests for step: {step_id}")

            # Get Step-Step dependencies with pagination
            next_token = ""
            while next_token is not None:
                step_dep_response = deadline.list_step_dependencies(
                    farmId=farm_id,
                    queueId=queue_id,
                    jobId=job_id,
                    stepId=step_id,
                    nextToken=next_token,
                )

                for dependent_step in step_dep_response["dependencies"]:
                    print_function_callback(
                        f"Found Step-Step dependency. {dependent_step['stepId']}"
                    )

                    # Get manifests for the step-step dependency
                    step_manifests_by_root: Dict[str, List[BaseAssetManifest]] = (
                        get_output_manifests_by_asset_root(
                            s3_settings=queue_s3_settings,
                            farm_id=farm_id,
                            queue_id=queue_id,
                            job_id=job_id,
                            step_id=dependent_step["stepId"],
                            session=queue_role_session,
                        )
                    )
                    # Merge all manifests by root.
                    for root in step_manifests_by_root.keys():
                        for manifest in step_manifests_by_root[root]:
                            print_function_callback(
                                f"Found step-step output manifest for root: {root}"
                            )
                            add_manifest_by_root(
                                manifests_by_root=manifests_by_root, root=root, manifest=manifest
                            )

                next_token = step_dep_response.get("nextToken")

    # If output manifests need to be downloaded
    if download_output:
        output_manifests_by_root: Dict[str, List[BaseAssetManifest]]
        if step_id is not None:
            print_function_callback(
                f"Downloading output manifests step: {step_id} of job: {job_id}"
            )
            # Only get the output manifests for selected step
            output_manifests_by_root = get_output_manifests_by_asset_root(
                s3_settings=queue_s3_settings,
                farm_id=farm_id,
                queue_id=queue_id,
                job_id=job_id,
                step_id=step_id,
                session=queue_role_session,
            )

        else:
            print_function_callback(f"Downloading output manifests for job: {job_id}")
            # Get output manifests for all steps of the job
            output_manifests_by_root = get_output_manifests_by_asset_root(
                s3_settings=queue_s3_settings,
                farm_id=farm_id,
                queue_id=queue_id,
                job_id=job_id,
                session=queue_role_session,
            )

        # Merge all output manifests by root.
        for root in output_manifests_by_root.keys():
            for manifest in output_manifests_by_root[root]:
                print_function_callback(f"Found output manifest for root: {root}")
                add_manifest_by_root(
                    manifests_by_root=manifests_by_root, root=root, manifest=manifest
                )

    # Finally, merge all manifest paths to create unified manifests.
    # TODO: Filter outputs by path

    merged_manifests: Dict[str, BaseAssetManifest] = {}
    for root in manifests_by_root.keys():
        merged_manifest = merge_asset_manifests(manifests_by_root[root])
        if merged_manifest:
            merged_manifests[root] = merged_manifest

    # Save the manifest files to disk.
    for root in merged_manifests.keys():
        # Save the merged manifest as {root}_{hash}_timestamp.
        root_hash: str = hash_data(
            root.encode("utf-8"), merged_manifests[root].get_default_hash_alg()
        )
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        manifest_name = root.replace("/", "_")
        manifest_name = manifest_name[1:] if manifest_name[0] == "_" else manifest_name
        manifest_name = f"{manifest_name}-{root_hash}-{timestamp}.manifest"

        local_manifest_file_path = os.path.join(download_dir, manifest_name)
        with open(local_manifest_file_path, "w") as file:
            file.write(merged_manifests[root].encode())
        successful_downloads.append(
            ManifestDownload(manifest_root=root, local_manifest_path=str(local_manifest_file_path))
        )
        print_function_callback(
            f"Downloaded merged manifest for root: {root} to: {local_manifest_file_path}"
        )

    # JSON output at the end.
    output = ManifestDownloadResponse(downloaded=successful_downloads)
    return output


def _manifest_merge(
    root: str,
    manifest_files: List[str],
    destination: str,
    name: Optional[str],
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> Optional[ManifestMerge]:
    """
    BETA API - API to merge multiple manifests into one.
    root: Root path for the manifest.
    manifest_files: List of manifest files to merge.
    destination: Destination directory for the merged manifest.
    name: Name of the merged manifest.
    print_function_callback: Callback function to handle print messages.
    return ManifestMerge object containing the merged manifest.
    """

    manifests: List[BaseAssetManifest] = list(
        _read_manifests(manifest_paths=manifest_files).values()
    )

    merged_manifest = merge_asset_manifests(manifests)

    if not merged_manifest:
        return None

    local_manifest_file = _write_manifest(
        root=root, manifest=merged_manifest, destination=destination, name=name
    )
    print_function_callback(f"Manifest generated at {local_manifest_file}")

    return ManifestMerge(manifest_root=root, local_manifest_path=local_manifest_file)
