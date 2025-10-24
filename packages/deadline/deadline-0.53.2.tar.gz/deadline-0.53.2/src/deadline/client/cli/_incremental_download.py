# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

__all__ = ["_incremental_output_download"]

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import difflib
from typing import Optional
from configparser import ConfigParser
from typing import Any, Callable
import sys
import time
import concurrent.futures
import textwrap

from .. import api
import boto3
from botocore.client import BaseClient  # type: ignore[import]
from ..exceptions import DeadlineOperationError
from ..api._list_jobs_by_filter_expression import _list_jobs_by_filter_expression
from ..api._session import get_session_client
from ...common.path_utils import summarize_path_list, human_readable_file_size
from ...job_attachments._incremental_downloads.incremental_download_state import (
    IncrementalDownloadState,
    IncrementalDownloadJob,
    _datetimes_to_str,
)
from ...job_attachments._incremental_downloads._manifest_s3_downloads import (
    _add_output_manifests_from_s3,
    _download_all_manifests_with_absolute_paths,
    _merge_absolute_path_manifest_list,
    _download_manifest_paths,
)
from ...job_attachments._path_mapping import _generate_path_mapping_rules, _PathMappingRuleApplier
from ...job_attachments.asset_manifests import (
    BaseAssetManifest,
    BaseManifestPath,
)
from ...job_attachments.asset_manifests import (
    HashAlgorithm,
)
from ...job_attachments.models import (
    FileConflictResolution,
    PathFormat,
    StorageProfileOperatingSystemFamily,
)
from ...job_attachments.progress_tracker import (
    ProgressReportMetadata,
)
from ._common import _cli_object_repr, sigint_handler


SESSIONS_API_MAX_CONCURRENCY = 3


@dataclass
class IncrementalOutputDownloadLatencies:
    """Dataclass for tracking latencies of operations in this command"""

    _get_download_candidate_jobs: int = 0
    _categorize_jobs_in_checkpoint: int = 0
    _get_job_sessions: int = 0
    _update_checkpoint_jobs_list: int = 0
    _download_all_manifests_with_absolute_paths: int = 0
    download: Optional[int] = None
    path_mapping: Optional[int] = None


def _get_download_candidate_jobs(
    boto3_session: boto3.Session,
    farm_id: str,
    queue_id: str,
    starting_timestamp: datetime,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> dict[str, dict[str, Any]]:
    """
    Uses deadline:SearchJobs queries to get a dict {job_id: job} of download candidates for the queue.
    This is a superset of all the jobs that have produced any output for download since
    the provided starting_timestamp.

    Args:
        boto3_session: The boto3.Session for accessing AWS.
        farm_id: The farm id for the operation.
        queue_id: The queue id for the operation.
        starting_timestamp: The point in time from which to look for new download outputs.
        print_function_callback: Callback for printing output to the terminal or log.

    Returns:
        A dictionary mapping job id to the job as returned by the deadline.search_jobs API.
    """
    print_function_callback("Retrieving updated data from Deadline Cloud...")
    start_time = datetime.now(tz=timezone.utc)

    # Construct the full set of jobs that may have new available downloads.
    # - Any active job (job with taskRunStatus in READY, ASSIGNED,
    #   STARTING, SCHEDULED, or RUNNING), that has at least one SUCCEEDED task.
    download_candidate_jobs = {
        job["jobId"]: job
        for job in _list_jobs_by_filter_expression(
            boto3_session,
            farm_id,
            queue_id,
            filter_expression={
                "filters": [
                    {
                        "stringFilter": {
                            "name": "TASK_RUN_STATUS",
                            "operator": "EQUAL",
                            "value": status_value,
                        },
                    }
                    # Maximum of 3 filters are permitted, so the 5 statuses are split
                    for status_value in ["READY", "ASSIGNED", "STARTING"]
                ],
                "operator": "OR",
            },
        )
    }
    download_candidate_jobs.update(
        {
            job["jobId"]: job
            for job in _list_jobs_by_filter_expression(
                boto3_session,
                farm_id,
                queue_id,
                filter_expression={
                    "filters": [
                        {
                            "stringFilter": {
                                "name": "TASK_RUN_STATUS",
                                "operator": "EQUAL",
                                "value": status_value,
                            },
                        }
                        for status_value in ["SCHEDULED", "RUNNING"]
                    ],
                    "operator": "OR",
                },
            )
        }
    )
    print(f"DEBUG: Got {len(download_candidate_jobs)} active jobs")
    download_candidate_jobs = {
        job_id: _datetimes_to_str(job)
        for job_id, job in download_candidate_jobs.items()
        if job["taskRunStatusCounts"]["SUCCEEDED"] > 0
    }
    print(
        f"DEBUG: Filtered down to {len(download_candidate_jobs)} active jobs based on SUCCEEDED task filter"
    )

    # - Any recently ended job (job went from active to terminal with a taskRunStatus
    #   in SUSPENDED, CANCELED, FAILED, SUCCEEDED, NOT_COMPATIBLE), that has at least
    #   one SUCCEEDED task. The endedAt timestamp field gets updated when that occurs.
    recently_ended_jobs = _list_jobs_by_filter_expression(
        boto3_session,
        farm_id,
        queue_id,
        filter_expression={
            "filters": [
                {
                    "dateTimeFilter": {
                        "name": "ENDED_AT",
                        "dateTime": starting_timestamp,
                        "operator": "GREATER_THAN_EQUAL_TO",
                    }
                }
            ],
            "operator": "AND",
        },
    )
    print(
        f"DEBUG: Got {len(recently_ended_jobs)} jobs with job[endedAt] >= {starting_timestamp.astimezone().isoformat()}"
    )
    # Filter to jobs where the count of SUCCEEDED tasks is positive.
    recently_ended_jobs = [
        job for job in recently_ended_jobs if job["taskRunStatusCounts"]["SUCCEEDED"] > 0
    ]
    print(f"DEBUG: Filtered down to {len(recently_ended_jobs)} jobs based on SUCCEEDED task filter")
    download_candidate_jobs.update(
        {job["jobId"]: _datetimes_to_str(job) for job in recently_ended_jobs}
    )

    duration = datetime.now(tz=timezone.utc) - start_time
    print_function_callback(f"...retrieval completed in {duration}")

    return download_candidate_jobs


class CategorizedJobIds:
    """
    Takes jobs loaded from a loaded checkpoint and a query to get download candidate jobs,
    analyzes all the jobs by looking at fields like task run status counds to categorize them.

    Job categories:
        added: The job was created or requeued so it now can produce new downloads.
        updated: The job changed since the previous incremental download operation.
        unchanged: The job did not change since the previous incremental download operation.
        completed: The job finished running so all output is available for download.
        inactive: The job can no longer have any new downloads unless it is requeued. Minimal
            metadata is tracked to detect if it is requeued.
        missing_storage_profile: The job has no storage profile, but the operation requires one.
            If incremental download was called with local_storage_profile_id=None, this set
            will always be empty.
        attachments_free: The job has no job attachments associated that can produce
            outputs for download.
    """

    added: set[str] = set()
    updated: set[str] = set()
    unchanged: set[str] = set()
    completed: set[str] = set()
    inactive: set[str] = set()
    missing_storage_profile: set[str] = set()
    attachments_free: set[str] = set()


def _categorize_jobs_in_checkpoint(
    boto3_session: boto3.Session,
    farm_id: str,
    queue_id: str,
    checkpoint: IncrementalDownloadState,
    download_candidate_jobs: dict[str, dict[str, Any]],
    new_completed_timestamp: datetime,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> CategorizedJobIds:
    """
    Categorizes the provided download candidate jobs by id into a CategorizedJobIds object,
    updating the jobs within download_candidate_jobs where necessary.

    * Calls boto3 deadline.get_job() to get job attachments manifest information and storage profile id if it is not stored yet.

    Args:
        boto3_session: The boto3.Session for accessing AWS.
        farm_id: The farm id for the operation.
        queue_id: The queue id for the operation.
        checkpoint: The checkpoint for the incremental download.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
        new_completed_timestamp: This is the timestamp value that will be placed in
            checkpoint.downloads_completed_timestamp when saving the checkpoint.
        print_function_callback: Callback for printing output to the terminal or log.
    """
    deadline = get_session_client(boto3_session, "deadline")
    checkpoint_jobs = {job.job_id: job.job for job in checkpoint.jobs}
    checkpoint_job_ids = set(checkpoint_jobs.keys())

    download_candidate_job_ids = set(download_candidate_jobs.keys())

    print_function_callback(
        f"Categorizing {len(checkpoint_jobs)} checkpoint jobs against {len(download_candidate_jobs)} download candidate jobs..."
    )
    start_time = datetime.now(tz=timezone.utc)

    finished_tracking_job_ids = checkpoint_job_ids.difference(download_candidate_job_ids)
    updated_job_ids = checkpoint_job_ids.intersection(download_candidate_job_ids)
    new_job_ids = download_candidate_job_ids.difference(checkpoint_job_ids)
    # The following sets get populated while analyzing the jobs
    unchanged_job_ids = set()
    attachments_free_job_ids = set()
    missing_storage_profile = set()
    completed_job_ids = set()

    # Copy the job attachments manifest data and storage profile id from the checkpoint to the new job objects. This data
    # is not returned by deadline:SearchJobs, so we need to call deadline:GetJob on every job to retrieve it. This data
    # on a job don't change, so after the call to deadline:GetJob we can cache it indefinitely.
    for job_id in updated_job_ids:
        ip_job = checkpoint_jobs[job_id]
        dc_job = download_candidate_jobs[job_id]

        if set(ip_job.keys()) == {"jobId"}:
            # If the job has a minimal placeholder, move the job id to the new job ids
            new_job_ids.add(job_id)
        elif ip_job["attachments"] is None:
            # Carry over the minimal placeholder identifying the job as not using job attachments
            download_candidate_jobs[job_id] = ip_job
            attachments_free_job_ids.add(job_id)
        elif ip_job["storageProfileId"] is None and checkpoint.local_storage_profile_id is not None:
            # Carry over the minimal placeholder identifying the job as missing a storage profile
            download_candidate_jobs[job_id] = ip_job
            missing_storage_profile.add(job_id)
        else:
            # Copy the attachments manifest metadata as it is not returned by deadline:SearchJobs
            dc_job["attachments"] = ip_job["attachments"]
            dc_job["storageProfileId"] = ip_job["storageProfileId"]

    updated_job_ids.difference_update(attachments_free_job_ids)
    updated_job_ids.difference_update(new_job_ids)
    updated_job_ids.difference_update(missing_storage_profile)

    # Prune jobs that we are (almost) certain have no changes by looking at its task status counts. We treat a job as unchanged if its
    # value job["taskRunStatusCounts"]["SUCCEEDED"] stayed the same and its timestamp job["endedAt"] stayed the same.
    #
    # The case this misses (and causes a delay in task output download) is the following sequence: 1/ User requeues one or more steps/tasks.
    # 2/ Tasks succeed in the correct number to equal the previous value 3/ The incremental output download command sees an equal count
    # and miscategorizes it as unchanged. If that count is all the tasks, the job["endedAt"] timestamp will catch it, and if the count
    # is less, the next time a task completes the succeeded count will be different.
    #
    # Because of this potential delay, the checkpoint needs to keep tracking all of the sessions it has seen, and cannot assume
    # that a session ending before the downloads completed timestamp was already processed.
    for job_id in updated_job_ids:
        ip_job = checkpoint_jobs[job_id]
        dc_job = download_candidate_jobs[job_id]

        if ip_job["taskRunStatusCounts"]["SUCCEEDED"] == dc_job["taskRunStatusCounts"][
            "SUCCEEDED"
        ] and ip_job.get("endedAt") == dc_job.get("endedAt"):
            print_function_callback(f"UNCHANGED Job: {dc_job['name']} ({job_id})")
            unchanged_job_ids.add(job_id)
    updated_job_ids.difference_update(unchanged_job_ids)

    # First make note of any jobs that were dropped from tracking, for example if they were canceled or they failed
    for job_id in finished_tracking_job_ids:
        ip_job = checkpoint_jobs[job_id]
        if "taskRunStatusCounts" in ip_job:
            ip_succeeded_task_count = ip_job["taskRunStatusCounts"]["SUCCEEDED"]
            ip_total_task_count = sum(value for _, value in ip_job["taskRunStatusCounts"].items())
        else:
            ip_succeeded_task_count = 0
            ip_total_task_count = -1

        # Print something only if the job is more than a minimal "jobId" tracker
        if set(ip_job.keys()) != {"jobId"}:
            print_function_callback(f"FINISHED TRACKING Job: {ip_job['name']} ({job_id})")
            if ip_job["attachments"] is None:
                print_function_callback("  Job without job attachments is no longer active")
            elif ip_succeeded_task_count == ip_total_task_count:
                print_function_callback("   Job succeeded")
            else:
                print_function_callback(
                    "   Job is not a download candidate anymore (likely suspended, canceled or failed)"
                )

    # Process all the jobs that have updates
    for job_id in updated_job_ids:
        ip_job = checkpoint_jobs[job_id]
        dc_job = download_candidate_jobs[job_id]
        ip_succeeded_task_count = ip_job["taskRunStatusCounts"]["SUCCEEDED"]
        ip_total_task_count = sum(value for _, value in ip_job["taskRunStatusCounts"].items())
        dc_succeeded_task_count = dc_job["taskRunStatusCounts"]["SUCCEEDED"]
        dc_total_task_count = sum(value for _, value in dc_job["taskRunStatusCounts"].items())

        print_function_callback(f"EXISTING Job: {ip_job['name']} ({job_id})")
        print_function_callback(
            f"  Succeeded tasks (before): {ip_succeeded_task_count} / {ip_total_task_count}"
        )
        print_function_callback(
            f"  Succeeded tasks (now)   : {dc_succeeded_task_count} / {dc_total_task_count}"
        )

        # Use the CLI output format to produce a diff of the changes
        ip_job_repr: list[str] = _cli_object_repr(ip_job).splitlines()
        dc_job_repr: list[str] = _cli_object_repr(dc_job).splitlines()

        for line in difflib.unified_diff(
            ip_job_repr,
            dc_job_repr,
            fromfile="Previous update",
            tofile="Current update",
            lineterm="",
        ):
            print_function_callback(f"  {line}")

        if (
            dc_succeeded_task_count == dc_total_task_count
            and "endedAt" in dc_job
            and datetime.fromisoformat(dc_job["endedAt"]) < new_completed_timestamp
        ):
            completed_job_ids.add(job_id)
    updated_job_ids.difference_update(completed_job_ids)

    # Process all the jobs that are new
    for job_id in new_job_ids:
        dc_job = download_candidate_jobs[job_id]

        # Call deadline:GetJob to retrieve attachments manifest information
        job = deadline.get_job(jobId=job_id, queueId=queue_id, farmId=farm_id)
        dc_job["attachments"] = job.get("attachments")
        dc_job["storageProfileId"] = job.get("storageProfileId")
        dc_succeeded_task_count = dc_job["taskRunStatusCounts"]["SUCCEEDED"]
        dc_total_task_count = sum(value for _, value in dc_job["taskRunStatusCounts"].items())

        print_function_callback(f"NEW Job: {dc_job['name']} ({job_id})")

        if (
            dc_job["attachments"] is not None
            and dc_job["storageProfileId"] is None
            and checkpoint.local_storage_profile_id is not None
        ):
            print_function_callback(
                "  WARNING: THE JOB OUTPUT WILL NOT BE DOWNLOADED, IT HAS NO STORAGE PROFILE."
            )
            missing_storage_profile.add(job_id)
            continue

        print_function_callback(
            f"  Succeeded tasks: {dc_succeeded_task_count} / {dc_total_task_count}"
        )
        if dc_job["attachments"] is None:
            # If the job does not use job attachments, save a minimal placeholder to avoid
            # repeatedly calling deadline:GetJob.
            download_candidate_jobs[job_id] = dc_job = {
                "jobId": job_id,
                "name": dc_job["name"],
                "attachments": None,
            }
            attachments_free_job_ids.add(job_id)
            print_function_callback("  Job does not use job attachments.")
        else:
            print_function_callback("  Manifest file system paths:")
            for manifest in dc_job["attachments"]["manifests"]:
                print_function_callback(
                    f"    - {manifest['rootPath']} ({manifest['rootPathFormat']})"
                )

        if (
            dc_succeeded_task_count == dc_total_task_count
            and "endedAt" in dc_job
            and datetime.fromisoformat(dc_job["endedAt"]) < new_completed_timestamp
        ):
            completed_job_ids.add(job_id)
    new_job_ids.difference_update(attachments_free_job_ids)
    new_job_ids.difference_update(completed_job_ids)
    new_job_ids.difference_update(missing_storage_profile)

    result = CategorizedJobIds()
    result.attachments_free = attachments_free_job_ids
    result.missing_storage_profile = missing_storage_profile
    result.completed = completed_job_ids
    result.inactive = finished_tracking_job_ids
    result.added = new_job_ids
    result.unchanged = unchanged_job_ids
    result.updated = updated_job_ids

    duration = datetime.now(tz=timezone.utc) - start_time
    print_function_callback(f"...categorization completed in {duration}")

    return result


def _retrieve_sessions_for_job(
    deadline_client: BaseClient,
    farm_id: str,
    queue_id: str,
    job_id: str,
    session_ended_threshold: datetime,
    output_job_sessions: dict[str, list],
):
    """
    Uses deadline.list_sessions to get all sessions of the specified job that are still running or
    that ended after session_ended_threshold.

    Places the output into output_job_sessions[job_id]

    Args:
        deadline_client: A boto3 client for accessing Deadline.
        farm_id: The farm id for the operation.
        queue_id: The queue id for the operation.
        job_id: The job id to process.
        session_ended_threshold: The timestamp threshold to filter out older sessions based on the endedAt field.
        output_job_sessions: A dictionary {job_id: session_list} to populate for the provided job id.
    """
    sessions_paginator = deadline_client.get_paginator("list_sessions")

    session_list: list[dict[str, Any]] = []
    for sessions_page in sessions_paginator.paginate(
        farmId=farm_id, queueId=queue_id, jobId=job_id
    ):
        for session in sessions_page.get("sessions", []):
            if "endedAt" not in session or session["endedAt"] >= session_ended_threshold:
                session_list.append(session)
    if session_list:
        output_job_sessions[job_id] = session_list


def _retrieve_session_actions_for_session(
    deadline_client: BaseClient,
    checkpoint_job_session_completed_indexes: dict[str, dict[str, int]],
    farm_id: str,
    queue_id: str,
    job_id: str,
    output_session: dict[str, Any],
):
    """
    Args:
        deadline_client: A boto3 client for accessing Deadline.
        checkpoint_job_session_completed_indexes: All the jobs' session action indexes loaded from the checkpoint.
            The value checkpoint_job_session_completed_indexes[job_id][session_id] is the session action index of
            the latest session action that is completed download.
        farm_id: The farm id for the operation.
        queue_id: The queue id for the operation.
        job_id: The job id to process.
        output_session: The session to populate with a sessionActions field.
    """
    session_actions_paginator = deadline_client.get_paginator("list_session_actions")

    session_action_list: list[dict[str, Any]] = []
    for session_actions_page in session_actions_paginator.paginate(
        farmId=farm_id,
        queueId=queue_id,
        jobId=job_id,
        sessionId=output_session["sessionId"],
    ):
        # Include only succeeded taskRun actions.
        for session_action in session_actions_page.get("sessionActions", []):
            succeeded = session_action.get("status") == "SUCCEEDED"
            is_task_run = "taskRun" in session_action.get("definition", {})
            if succeeded and is_task_run:
                session_action_list.append(session_action)

    if session_action_list:
        # Extract the session action indexes from the ids
        for session_action in session_action_list:
            # Session action IDs look like "sessionaction-abc123-12" for index 12
            session_action_index = int(session_action["sessionActionId"].rsplit("-", 1)[-1])
            session_action["sessionActionIndex"] = session_action_index
        # Include only session action indexes newer than latest downloaded ones from the checkpoint
        session_completed_index: Optional[int] = checkpoint_job_session_completed_indexes.get(
            job_id, {}
        ).get(output_session["sessionId"])
        if session_completed_index is not None:
            # Filter out older session actions that were already downloaded
            session_action_list = [
                session_action
                for session_action in session_action_list
                if session_action["sessionActionIndex"] > session_completed_index
            ]
        if session_action_list:
            output_session["sessionActions"] = session_action_list


def _get_job_sessions(
    boto3_session: boto3.Session,
    boto3_session_for_s3: boto3.Session,
    farm_id: str,
    queue: dict[str, Any],
    checkpoint_job_session_completed_indexes: dict[str, dict[str, int]],
    categorized_job_ids: CategorizedJobIds,
    checkpoint: IncrementalDownloadState,
    download_candidate_jobs: dict[str, dict[str, Any]],
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> dict[str, list]:
    """
    This function gets all the job sessions and session actions from the completed, added, and updated jobs.
    It uses the checkpoint's session_completed_indexes to filter out older session actions that are already downloaded.

    Args:
        boto3_session: The boto3.Session for accessing AWS.
        boto3_session_for_s3: The boto3.Session to use for accessing S3.
        farm_id: The farm id for the operation.
        queue: The queue as returned by boto3 deadline.get_queue().
        checkpoint_job_session_completed_indexes: All the jobs' session action indexes loaded from the checkpoint.
            The value checkpoint_job_session_completed_indexes[job_id][session_id] is the session action index of
            the latest session action that is completed download.
        categorized_job_ids: The categorized job ids as returned by _categorize_jobs_in_checkpoint().
        checkpoint: The checkpoint for the incremental download.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
        print_function_callback: Callback for printing output to the terminal or log.

    Returns:
        Access a session action in the returned job_sessions with
            job_sessions[job_id][session_index]["sessionActions"][session_action_index]
        The returned structure looks like this:
        {
            "<job_id>": [
                {
                    "sessionId": "<session_id>",
                    ...,
                    "sessionActions": [
                        {
                            "sessionActionId": "<session_action_id>",
                            ...
                        },
                        ...
                    ]
                },
                ...
            ],
            ...
        }
    """
    job_ids = categorized_job_ids.completed.union(categorized_job_ids.added).union(
        categorized_job_ids.updated
    )
    print_function_callback(f"Retrieving sessions for {len(job_ids)} jobs...")
    start_time = datetime.now(tz=timezone.utc)

    # The max timestamp of a downloaded session's endedAt provides a lower bound to filter sessions by.
    # This is tracked in the checkpoint.
    job_session_ended_timestamp: dict[str, datetime] = {
        job.job_id: job.session_ended_timestamp
        for job in checkpoint.jobs
        if job.session_ended_timestamp is not None
    }

    deadline = get_session_client(boto3_session, "deadline")
    job_sessions: dict[str, list] = {}

    # Retrieve all the sessions with some parallelism
    max_workers = SESSIONS_API_MAX_CONCURRENCY
    print_function_callback(f"Using {max_workers} threads")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for job_id in job_ids:
            # Use the greater of the bootstrap command timestamp and the session ended timestamps
            # recorded in the checkpoint.
            session_ended_threshold = job_session_ended_timestamp.get(job_id)
            if session_ended_threshold is None:
                session_ended_threshold = checkpoint.downloads_started_timestamp

            # For all jobs that are not NEW (including re-queued jobs) - i.e. completed and updated jobs
            # Use an eventual consistency window to accept a little extra
            if job_id not in categorized_job_ids.added:
                session_ended_threshold = session_ended_threshold - timedelta(
                    seconds=checkpoint.eventual_consistency_max_seconds
                )

            futures.append(
                executor.submit(
                    _retrieve_sessions_for_job,
                    deadline,
                    farm_id,
                    queue["queueId"],
                    job_id,
                    session_ended_threshold,
                    job_sessions,
                )
            )

        # surfaces any exceptions in the thread
        for future in concurrent.futures.as_completed(futures):
            future.result()

    duration = datetime.now(tz=timezone.utc) - start_time
    print_function_callback(f"...retrieval completed in {duration}")

    print_function_callback("")
    print_function_callback(
        f"Retrieving session actions for {sum(len(session_list) for session_list in job_sessions.values())} sessions..."
    )
    start_time = datetime.now(tz=timezone.utc)

    # Retrieve all the session actions with some parallelism
    max_workers = SESSIONS_API_MAX_CONCURRENCY
    print_function_callback(f"Using {max_workers} threads")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for job_id, session_list in job_sessions.items():
            for session in session_list:
                futures.append(
                    executor.submit(
                        _retrieve_session_actions_for_session,
                        deadline,
                        checkpoint_job_session_completed_indexes,
                        farm_id,
                        queue["queueId"],
                        job_id,
                        session,
                    )
                )
        # surfaces any exceptions in the thread
        for future in concurrent.futures.as_completed(futures):
            future.result()

    duration = datetime.now(tz=timezone.utc) - start_time
    print_function_callback(f"...retrieval completed in {duration}")

    print_function_callback("")
    print_function_callback("Populating missing manifest S3 keys...")
    start_time = datetime.now(tz=timezone.utc)

    _add_missing_output_manifests_to_job_sessions(
        boto3_session_for_s3, farm_id, queue, job_sessions, download_candidate_jobs
    )

    _filter_session_actions_without_manifests_from_job_sessions(
        job_sessions,
        download_candidate_jobs,
        print_function_callback,
    )

    duration = datetime.now(tz=timezone.utc) - start_time
    print_function_callback(f"...populated in {duration}")

    return job_sessions


def _get_storage_profiles(
    deadline: BaseClient,
    farm_id: str,
    queue: dict[str, Any],
    job_sessions: dict[str, list],
    checkpoint: IncrementalDownloadState,
    download_candidate_jobs: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Retrieves all the needed storage profiles. To call this function,
    checkpoint.local_storage_profile_id must be set.

    Args:
        deadline: An AWS client for calling deadline APIs.
        farm_id: The farm id for the operation.
        queue: The queue as returned by boto3 deadline.get_queue().
        checkpoint: The checkpoint for the incremental download.
        job_sessions: Contains each job's sessions and session actions, structured as job_sessions[job_id][session_index]["sessionActions"][session_action_index].
                      See the function _get_job_sessions for more details.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
    """
    if checkpoint.local_storage_profile_id is None:
        raise ValueError("The checkpoint local storage profile id must be set.")

    # Collect all the storage profile ids
    storage_profile_ids: set[str] = {checkpoint.local_storage_profile_id}
    for job_id in job_sessions.keys():
        storage_profile_ids.add(download_candidate_jobs[job_id]["storageProfileId"])

    # Load all the storage profiles from Deadline Cloud
    storage_profiles = {
        storage_profile_id: deadline.get_storage_profile_for_queue(
            farmId=farm_id,
            queueId=queue["queueId"],
            storageProfileId=storage_profile_id,
        )
        for storage_profile_id in storage_profile_ids
    }

    return storage_profiles


def _create_path_mapping_rule_appliers(
    storage_profiles: dict[str, dict[str, Any]],
    checkpoint: IncrementalDownloadState,
    download_candidate_jobs: dict[str, dict[str, Any]],
    print_function_callback: Callable[[Any], None] = lambda msg: None,
) -> dict[str, Optional[_PathMappingRuleApplier]]:
    """
    Retrieves all the needed storage profiles and constructs path mapping rule applies for them.
    To call this function, checkpoint.local_storage_profile_id must be set.

    Args:
        storage_profiles: A mapping from storage profile id to the storage profile as returned by boto3 deadline.get_storage_profile_for_queue.
        checkpoint: The checkpoint for the incremental download.
        job_sessions: Contains each job's sessions and session actions, structured as job_sessions[job_id][session_index]["sessionActions"][session_action_index].
                      See the function _get_job_sessions for more details.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
        print_function_callback: Callback for printing output to the terminal or log.
    """
    if checkpoint.local_storage_profile_id is None:
        raise ValueError("The checkpoint local storage profile id must be set.")

    path_mapping_rule_appliers: dict[str, Optional[_PathMappingRuleApplier]] = {}

    # Create a path mapping rule applier for each storage profile
    local_storage_profile = storage_profiles[checkpoint.local_storage_profile_id]
    local_storage_profile_name = local_storage_profile["displayName"]
    print_function_callback("")
    print_function_callback(
        f"Local storage profile is {local_storage_profile_name} ({checkpoint.local_storage_profile_id})"
    )
    print_function_callback(
        f"  {len([job for job in download_candidate_jobs.values() if job.get('storageProfileId') == checkpoint.local_storage_profile_id])} download candidate jobs have the same storage profile and will be downloaded to their original specified paths"
    )
    for storage_profile_id, storage_profile in storage_profiles.items():
        storage_profile_name = storage_profile["displayName"]
        if storage_profile_id == checkpoint.local_storage_profile_id:
            path_mapping_rule_appliers[storage_profile_id] = None
        else:
            rules = _generate_path_mapping_rules(storage_profile, local_storage_profile)
            path_mapping_rule_appliers[storage_profile_id] = _PathMappingRuleApplier(rules)

            # Print the path mapping rules for each source storage profile
            print_function_callback("")
            job_count = len(
                [
                    job
                    for job in download_candidate_jobs.values()
                    if job.get("storageProfileId") == storage_profile_id
                ]
            )
            print_function_callback(
                f"Path mapping rules for {job_count} download candidate jobs with storage profile {storage_profile_name} ({storage_profile_id})"
            )
            print_function_callback(
                f"  job storage profile: {storage_profile_name} ({storage_profile['osFamily']})"
            )
            print_function_callback(
                f"  local storage profile: {local_storage_profile_name} ({local_storage_profile['osFamily']})"
            )
            if rules:
                for rule in rules:
                    print_function_callback(f"  - from: {rule.source_path}")
                    print_function_callback(f"    to:   {rule.destination_path}")
            else:
                print_function_callback(
                    f"   No rules generated. Storage profiles {local_storage_profile_name} and {storage_profile_name} share no file system location names."
                )
    return path_mapping_rule_appliers


def _add_missing_output_manifests_to_job_sessions(
    boto3_session_for_s3: boto3.Session,
    farm_id: str,
    queue: dict[str, Any],
    job_sessions: dict[str, list],
    download_candidate_jobs: dict[str, dict[str, Any]],
):
    """
    Args:
        boto3_session_for_s3: The boto3.Session to use for accessing S3.
        farm_id: The farm id for the operation.
        queue: The queue as returned by boto3 deadline.get_queue().
        job_sessions: Contains each job's sessions and session actions, structured as job_sessions[job_id][session_index]["sessionActions"][session_action_index].
                      See the function _get_job_sessions for more details.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
    """
    for job_id, session_list in job_sessions.items():
        job = download_candidate_jobs[job_id]
        session_action_list = [
            session_action
            for session in session_list
            for session_action in session.get("sessionActions", [])
        ]
        _add_output_manifests_from_s3(
            farm_id, queue, job, boto3_session_for_s3, session_action_list
        )


def _filter_session_actions_without_manifests_from_job_sessions(
    job_sessions: dict[str, list],
    download_candidate_jobs: dict[str, dict[str, Any]],
    print_function_callback: Callable[[Any], None] = lambda msg: None,
):
    """
    Modify job_sessions in place to filter out any session actions that lack any output manifests.
    Print a warning message for any job that had a session action like this.

    Args:
        job_sessions: Contains each job's sessions and session actions, structured as job_sessions[job_id][session_index]["sessionActions"][session_action_index].
                      See the function _get_job_sessions for more details.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
        print_function_callback: Callback for printing output to the terminal or log.
    """
    for job_id, session_list in job_sessions.items():
        job = download_candidate_jobs[job_id]
        total_count = 0
        filtered_count = 0
        for session in session_list:
            total_count += len(session.get("sessionActions", []))
            # Filter out session actions with no manifest files
            filtered_session_action_list = [
                session_action
                for session_action in session.get("sessionActions", [])
                if any(item != {} for item in session_action["manifests"])
            ]
            filtered_count += len(filtered_session_action_list)
            if total_count != filtered_count:
                session["sessionActions"] = filtered_session_action_list
        if total_count != filtered_count:
            print_function_callback(
                f"WARNING: Job {job['name']} ({job_id}) ran {total_count - filtered_count} / {total_count} session actions with no output."
            )
            print_function_callback(
                "         This may indicate steps in the job that strictly perform validation or save results elsewhere like a shared file system or S3."
            )


def _update_checkpoint_jobs_list(
    checkpoint: IncrementalDownloadState,
    download_candidate_jobs: dict[str, dict[str, Any]],
    categorized_job_ids: CategorizedJobIds,
    job_sessions: dict[str, list],
):
    """
    Update the jobs list in the checkpoint object.

    Args:
        checkpoint: The checkpoint for the incremental download.
        download_candidate_jobs: The result of a _get_download_candidate_jobs call, {job_id: job} where
            job is a result from a deadline.search_jobs() or deadline.get_job() call.
        categorized_job_ids: The categorized job ids as returned by _categorize_jobs_in_checkpoint().
        job_sessions: Contains each job's sessions and session actions, structured as job_sessions[job_id][session_index]["sessionActions"][session_action_index].
                      See the function _get_job_sessions for more details.
    """
    updated_jobs: list[IncrementalDownloadJob] = []

    # Produce the session_ended_timestamp for all the job ids. Start
    # with the values from the previous checkpoint, and then overwrite
    # them from job_sessions
    job_session_ended_timestamps: dict[str, Optional[datetime]] = {
        job.job_id: job.session_ended_timestamp
        for job in checkpoint.jobs
        if job.session_ended_timestamp is not None
    }
    for job_id, session_list in job_sessions.items():
        max_session_ended_timestamp = None
        for session in session_list:
            if "endedAt" in session:
                if max_session_ended_timestamp is None:
                    max_session_ended_timestamp = session["endedAt"]
                else:
                    max_session_ended_timestamp = max(
                        max_session_ended_timestamp, session["endedAt"]
                    )
        job_session_ended_timestamps[job_id] = max_session_ended_timestamp

    # Produce the session_completed_indexes for all the job ids. Start
    # with the values from the previous checkpoint, then overwrite
    # them from job_sessions.
    job_session_completed_indexes: dict[str, dict[str, int]] = {
        job.job_id: job.session_completed_indexes for job in checkpoint.jobs
    }
    for job_id, session_list in job_sessions.items():
        for session in session_list:
            session_actions = session.get("sessionActions", [])
            if session_actions:
                job_session_completed_indexes.setdefault(job_id, {})[session["sessionId"]] = max(
                    session_action["sessionActionIndex"] for session_action in session_actions
                )
        job_session_ended_timestamps[job_id] = max_session_ended_timestamp

    # These categories keep the download_candidate_jobs job as is.
    for job_id in (
        categorized_job_ids.added | categorized_job_ids.updated | categorized_job_ids.unchanged
    ):
        updated_jobs.append(
            IncrementalDownloadJob(
                download_candidate_jobs[job_id],
                job_session_ended_timestamps.get(job_id),
                job_session_completed_indexes.get(job_id, {}),
            )
        )
    # This category keeps a signal that it has no job attachments to process by having an attachments field with None in it
    for job_id in categorized_job_ids.attachments_free:
        updated_jobs.append(
            IncrementalDownloadJob(
                {
                    "jobId": job_id,
                    "name": download_candidate_jobs[job_id]["name"],
                    "attachments": None,
                },
                None,
                {},
            )
        )
    # This category keeps a signal that it is missing a storage profile by populating the attachments but
    # having a storageProfileId field with None in it. By keeping the attachments in the checkpoint, someone
    # inspecting the checkpoint to understand what's happening can get an idea about the paths for the job
    # and diagnose problems quicker.
    for job_id in categorized_job_ids.missing_storage_profile:
        updated_jobs.append(
            IncrementalDownloadJob(
                {
                    "jobId": job_id,
                    "name": download_candidate_jobs[job_id]["name"],
                    "attachments": download_candidate_jobs[job_id]["attachments"],
                    "storageProfileId": None,
                },
                None,
                {},
            )
        )
    # Keep completed jobs around until they become inactive
    for job_id in categorized_job_ids.completed:
        updated_jobs.append(
            IncrementalDownloadJob(
                download_candidate_jobs[job_id],
                job_session_ended_timestamps.get(job_id),
                job_session_completed_indexes.get(job_id, {}),
            )
        )
    # When a job becomes inactive, keep it around in minimal form when it has a session_ended_timestamp.
    # This is necessary for the case where a completed job gets requeued later. We can't tell
    # that it was requeued from the deadline.search_jobs query, so we hold this metadata in the checkpoint.
    for job_id in categorized_job_ids.inactive:
        session_ended_timestamp = job_session_ended_timestamps.get(job_id)
        if session_ended_timestamp is not None:
            updated_jobs.append(
                IncrementalDownloadJob({"jobId": job_id}, session_ended_timestamp, {})
            )

    checkpoint.jobs = updated_jobs


@api.record_function_latency_telemetry_event()
def _incremental_output_download(
    farm_id: str,
    queue: dict[str, Any],
    boto3_session: boto3.Session,
    checkpoint: IncrementalDownloadState,
    file_conflict_resolution: FileConflictResolution,
    config: Optional[ConfigParser] = None,
    print_function_callback: Callable[[Any], None] = lambda msg: None,
    *,
    dry_run: bool = False,
) -> IncrementalDownloadState:
    """
    This function downloads all the task run outputs from the specified queue, that have become
    available since the last time the function was called. The checkpoint object
    keeps track of all state needed to keep track of what needs to be downloaded.

    Pre-condition: The input checkpoint holds all information needed to understand the state of downloads
        completed up to the timestamp checkpoint.downloads_completed_timestamp. See the documentation
        in the IncrementalDownloadState to understand the invariants of the checkpoint.

    Post-condition: The output checkpoint has an updated checkpoint.downloads_completed_timestamp,
        all downloads were performed up to at least this timestamp, and the checkpoint data
        is updated to satisfy the next call's pre-condition.

    Args:
        farm_id: The farm id for the operation.
        queue: The queue as returned by boto3 deadline.get_queue().
        boto3_session: The boto3.Session for accessing AWS.
        checkpoint: The checkpoint for the incremental download.
        config: Optional, a Deadline Cloud configuration as loaded from config_file.read_config().
        print_function_callback: Callback for printing output to the terminal or log.
        dry_run: If True, the operation will print out information but not perform any data downloads.

    Returns:
        An updated checkpoint object.
    """
    if sys.version_info < (3, 9):
        raise DeadlineOperationError("The sync-output command requires Python version 3.9 or later")

    durations = IncrementalOutputDownloadLatencies()
    deadline = get_session_client(boto3_session, "deadline")

    # When this function is done, we will be confident that downloads are complete up to
    # new_completed_timestamp. We subtract a duration from now() that gives a generous amount of
    # time for the deadline:SearchJobs API's eventual consistency to converge.
    current_timestamp = datetime.now(timezone.utc)
    new_completed_timestamp = max(
        checkpoint.downloads_started_timestamp,
        current_timestamp - timedelta(seconds=checkpoint.eventual_consistency_max_seconds),
    )

    # The queue role is used for accessing S3
    boto3_session_for_s3 = api.get_queue_user_boto3_session(
        deadline=deadline,
        config=config,
        farm_id=farm_id,
        queue_id=queue["queueId"],
        queue_display_name=queue["displayName"],
    )

    print_function_callback("Updating download state across time interval:")
    print_function_callback(
        f"    From: {checkpoint.downloads_completed_timestamp.astimezone().isoformat()}"
    )
    print_function_callback(f"      To: {current_timestamp.astimezone().isoformat()}")
    update_length = current_timestamp - checkpoint.downloads_completed_timestamp
    eventual_consistency_delta = timedelta(seconds=checkpoint.eventual_consistency_max_seconds)
    if update_length > eventual_consistency_delta:
        print_function_callback(
            f"  Length: {update_length - eventual_consistency_delta} + {eventual_consistency_delta} (eventual consistency allowance)"
        )
    else:
        # Immediately after bootstrapping, this length will be shorter than the eventual consistency window
        print_function_callback(f"  Length: {update_length}")
    print_function_callback("")

    # Save all the jobs' session action indexes from the checkpoint, before we update the checkpoint's jobs list
    checkpoint_job_session_completed_indexes: dict[str, dict[str, int]] = {
        job.job_id: job.session_completed_indexes for job in checkpoint.jobs
    }

    # Call deadline:SearchJobs to get a set of jobs that includes every job with downloads available.
    start_t = time.perf_counter_ns()
    download_candidate_jobs: dict[str, dict[str, Any]] = _get_download_candidate_jobs(
        boto3_session,
        farm_id,
        queue["queueId"],
        checkpoint.downloads_completed_timestamp,
        print_function_callback,
    )
    durations._get_download_candidate_jobs = time.perf_counter_ns() - start_t

    print_function_callback("")

    # Compare the download candidates with the previously saved checkpoint state to categorize the jobs
    start_t = time.perf_counter_ns()
    categorized_job_ids: CategorizedJobIds = _categorize_jobs_in_checkpoint(
        boto3_session,
        farm_id,
        queue["queueId"],
        checkpoint,
        download_candidate_jobs,
        new_completed_timestamp,
        print_function_callback,
    )
    durations._categorize_jobs_in_checkpoint = time.perf_counter_ns() - start_t

    print_function_callback("")

    # All the completed, added, and updated jobs might have downloads available. Retrieve the sessions for these jobs.
    start_t = time.perf_counter_ns()
    job_sessions: dict[str, list] = _get_job_sessions(
        boto3_session,
        boto3_session_for_s3,
        farm_id,
        queue,
        checkpoint_job_session_completed_indexes,
        categorized_job_ids,
        checkpoint,
        download_candidate_jobs,
        print_function_callback,
    )
    durations._get_job_sessions = time.perf_counter_ns() - start_t

    # If storage profiles are being used, get them and construct all the path mapping rules
    path_mapping_rule_appliers: dict[str, Optional[_PathMappingRuleApplier]] = {}
    if checkpoint.local_storage_profile_id:
        start_t = time.perf_counter_ns()
        storage_profiles = _get_storage_profiles(
            deadline, farm_id, queue, job_sessions, checkpoint, download_candidate_jobs
        )
        path_mapping_rule_appliers = _create_path_mapping_rule_appliers(
            storage_profiles,
            checkpoint,
            download_candidate_jobs,
            print_function_callback,
        )
        durations.path_mapping = time.perf_counter_ns() - start_t

    # Use the information collected so far to update the jobs list in checkpoint
    start_t = time.perf_counter_ns()
    _update_checkpoint_jobs_list(
        checkpoint, download_candidate_jobs, categorized_job_ids, job_sessions
    )
    durations._update_checkpoint_jobs_list = time.perf_counter_ns() - start_t

    start_t = time.perf_counter_ns()
    unmapped_paths: dict[str, list[str]] = {}
    downloaded_manifests: list[tuple[datetime, BaseAssetManifest]] = (
        _download_all_manifests_with_absolute_paths(
            queue,
            download_candidate_jobs,
            job_sessions,
            path_mapping_rule_appliers,
            unmapped_paths,
            boto3_session_for_s3,
            print_function_callback,
        )
    )
    durations._download_all_manifests_with_absolute_paths = time.perf_counter_ns() - start_t

    # Print warning messages about all the output paths that will not be downloaded due to lack of path mapping.
    if unmapped_paths:
        print_function_callback("")
        print_function_callback("WARNING: THE FOLLOWING FILES WILL NOT BE DOWNLOADED")
        for job_id, unmapped_path_list in unmapped_paths.items():
            print_function_callback(
                f"    Job {download_candidate_jobs[job_id]['name']} ({job_id}) has outputs with unmapped paths that will not be downloaded"
            )
            storage_profile = storage_profiles[download_candidate_jobs[job_id]["storageProfileId"]]
            print_function_callback(
                f"      Job storage profile is {storage_profile['displayName']} ({storage_profile['storageProfileId']})"
            )
            print_function_callback("      Summary of unmapped paths:")
            path_format = (
                PathFormat.WINDOWS
                if storage_profile["osFamily"] == StorageProfileOperatingSystemFamily.WINDOWS.value
                else PathFormat.POSIX
            )
            paths_summary = summarize_path_list(
                unmapped_path_list, max_entries=30, path_format=path_format
            )
            print_function_callback(textwrap.indent(paths_summary, "      "))

    # Merge the manifests ordered by the last modified timestamp
    manifest_paths_to_download: list[BaseManifestPath] = _merge_absolute_path_manifest_list(
        downloaded_manifests
    )

    # Print a summary of all the paths before starting the download
    local_path_list = [manifest_path.path for manifest_path in manifest_paths_to_download]
    file_size_by_path = {
        manifest_path.path: manifest_path.size for manifest_path in manifest_paths_to_download
    }
    print_function_callback("")
    print_function_callback("Summary of paths to download:")
    print_function_callback(
        summarize_path_list(local_path_list, total_size_by_path=file_size_by_path, max_entries=30)
    )
    print_function_callback("")

    if not dry_run:
        print_function_callback(f"Downloading {len(manifest_paths_to_download)} files from S3...")
        start_t = time.perf_counter_ns()
        start_time = datetime.now(tz=timezone.utc)

        # Incremental download is mostly a background thing, so don't print status too often while downloading
        MIN_DELAY_BETWEEN_PRINTOUTS = 20
        last_call_time = time.time() - MIN_DELAY_BETWEEN_PRINTOUTS
        printed_100_percent = False

        def _update_download_progress(
            download_metadata: ProgressReportMetadata,
        ) -> bool:
            nonlocal last_call_time, printed_100_percent

            if not printed_100_percent and download_metadata.progress == 100:
                print_function_callback(f"{download_metadata.progressMessage}")
                last_call_time = time.time()
                printed_100_percent = True
            elif (
                not printed_100_percent
                and time.time() - last_call_time > MIN_DELAY_BETWEEN_PRINTOUTS
            ):
                print_function_callback(f"{download_metadata.progressMessage}")
                last_call_time = time.time()

            return sigint_handler.continue_operation

        _download_manifest_paths(
            manifest_paths_to_download,
            HashAlgorithm.XXH128,
            queue,
            boto3_session_for_s3,
            file_conflict_resolution,
            on_downloading_files=_update_download_progress,
            print_function_callback=print_function_callback,
        )

        durations.download = time.perf_counter_ns() - start_t
        duration = datetime.now(tz=timezone.utc) - start_time
        print_function_callback(f"...downloaded in {duration}")
    else:
        print_function_callback("Skipping downloads due to DRY RUN")

    # Update the timestamp in the state object to reflect the downloads that were completed
    checkpoint.downloads_completed_timestamp = new_completed_timestamp

    stats: dict[str, Any] = {
        "downloaded_session_actions": sum(
            len(session.get("sessionActions", []))
            for session_list in job_sessions.values()
            for session in session_list
        ),
        "downloaded_files": len(manifest_paths_to_download),
        "downloaded_bytes": sum(path.size for path in manifest_paths_to_download),
        "jobs_with_downloads": {
            "completed": len(categorized_job_ids.completed),
            "added": len(categorized_job_ids.added),
            "updated": len(categorized_job_ids.updated),
        },
        "jobs_without_downloads": {
            "not_using_job_attachments": len(categorized_job_ids.attachments_free),
            "missing_storage_profile": len(categorized_job_ids.missing_storage_profile),
            "unchanged": len(categorized_job_ids.unchanged),
            "inactive": len(categorized_job_ids.inactive),
        },
        "unmapped_paths": len(unmapped_paths),
    }
    api.get_deadline_cloud_library_telemetry_client().record_event(
        event_type="com.amazon.rum.deadline.queue_sync_output_stats",
        event_details={
            "latencies": asdict(durations),
            "dry_run": dry_run,
            **stats,
        },
    )

    print_function_callback("")
    if dry_run:
        print_function_callback(
            "Summary of DRY RUN for incremental output download (no files were downloaded to the file system):"
        )
    else:
        print_function_callback("Summary of incremental output download:")
    print_function_callback(f"  Downloaded session actions: {stats['downloaded_session_actions']}")
    print_function_callback(f"  Downloaded files: {stats['downloaded_files']}")
    print_function_callback(
        f"  Downloaded bytes: {human_readable_file_size(stats['downloaded_bytes'])}"
    )
    print_function_callback("  Jobs with downloads:")
    print_function_callback(f"    completed: {stats['jobs_with_downloads']['completed']}")
    print_function_callback(f"    added: {stats['jobs_with_downloads']['added']}")
    print_function_callback(f"    updated: {stats['jobs_with_downloads']['updated']}")
    print_function_callback("  Jobs without downloads:")
    print_function_callback(
        f"    not using job attachments: {stats['jobs_without_downloads']['not_using_job_attachments']}"
    )
    print_function_callback(
        f"    missing storage profile: {stats['jobs_without_downloads']['missing_storage_profile']}"
    )
    print_function_callback(f"    unchanged: {stats['jobs_without_downloads']['unchanged']}")
    print_function_callback(f"    inactive: {stats['jobs_without_downloads']['inactive']}")

    return checkpoint
