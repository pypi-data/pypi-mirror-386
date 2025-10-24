import os
import shutil
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import JSONDecodeError
from math import ceil
from pathlib import Path
from typing import Any

import hostile
import httpx
from httpx import Response
from rich_click import secho

import gpas
from gpas import models, util
from gpas.client import env
from gpas.client.upload_client import UploadAPIClient
from gpas.constants import (
    DEFAULT_APP_HOST,
    DEFAULT_CHUNK_SIZE,
)
from gpas.http_helpers import request_with_redirects
from gpas.log_utils import httpx_hooks, logger
from gpas.types import (
    OnComplete,
    OnProgress,
    PipelineVersion,
    PreparedFile,
    Sample,
    UploadData,
    UploadingFile,
    UploadSession,
)


def prepare_upload_files(
    target_filepath: Path, sample_id: str, read_num: int, decontaminated: bool = False
) -> Path:
    """Rename the files to be compatible with what the server is expecting.

    Which is `*_{1,2}.fastq.gz` and
    gzip the file if it isn't already,
    which should only be if the files haven't been run through Hostile.

    Args:
        target_filepath (Path): The target file path.
        sample_id (str): The sample ID.
        read_num (int): The read number.
        decontaminated (bool): Whether the files are decontaminated.

    Returns:
        Path: The prepared file path.
    """
    new_reads_filename = f"{sample_id}_{read_num}.fastq.gz"
    if decontaminated:
        upload_filepath = target_filepath.rename(
            target_filepath.with_name(new_reads_filename)
        )
    else:
        if target_filepath.suffix != ".gz":
            upload_filepath = util.gzip_file(target_filepath, new_reads_filename)
        else:
            upload_filepath = shutil.copyfile(
                target_filepath, target_filepath.with_name(new_reads_filename)
            )
    return upload_filepath


def create_batch_on_server(
    batch: models.UploadBatch,
    amplicon_scheme: str | None,
) -> tuple[str, str, str]:
    """Create batch on server, return batch id.

    A transaction will be created at this point for the expected
    total samples in the BatchModel.

    Args:
        host (str): The host server.
        number_of_samples (int): The expected number of samples in the batch.
        amplicon_scheme (str | None): The amplicon scheme to use.

    Returns:
        tuple[str, str, str]: The batch ID, batch name, and legacy batch ID.
    """
    client = UploadAPIClient()

    # Assume every sample in batch has same collection date and country etc
    instrument_platform = batch.samples[0].instrument_platform
    collection_date = batch.samples[0].collection_date
    country = batch.samples[0].country
    telemetry_data = {
        "client": {
            "name": "gpas-client",
            "version": gpas.__version__,
        },
        "decontamination": {
            "name": "hostile",
            "version": hostile.__version__,
        },
        "specimen_organism": batch.samples[0].specimen_organism,
    }

    batch_name = (
        batch.samples[0].batch_name
        if batch.samples[0].batch_name not in ["", " ", None]
        else f"batch_{collection_date}"
    )
    data = {
        "collection_date": str(collection_date),
        "instrument": instrument_platform,
        "country": country,
        "name": batch_name,
        "amplicon_scheme": amplicon_scheme,
        "telemetry_data": telemetry_data,
        "pipeline_version": batch.pipeline_version,
    }

    try:
        response = client.create_batches(data)
        # Get generated batch name for mapping CSV
        legacy_batch_id = response["legacy_batch_id"]
        with httpx.Client(
            event_hooks=httpx_hooks,
            transport=httpx.HTTPTransport(retries=5),
            timeout=60,
        ) as client:
            legacy_batch_response = request_with_redirects(
                client,
                "GET",
                f"{env.get_protocol()}://{env.get_host()}/api/v1/batches/{legacy_batch_id}",
                headers={
                    "Authorization": f"Bearer {env.get_access_token(env.get_host())}",
                    "accept": "application/json",
                },
            )
            legacy_batch = legacy_batch_response.json()

        return (response["id"], legacy_batch["name"], legacy_batch_id)

    except JSONDecodeError:
        logger.error(
            f"Unable to communicate with the upload endpoint ({client.base_url}). Please check this has been set "
            f"correctly and try again."
        )
        exit(1)


def upload_batch(
    batch: models.UploadBatch,
    skip_decontamination: bool,
    save: bool = False,
) -> None:
    """Upload a batch of samples.

    Args:
        batch (models.UploadBatch): The batch of samples to upload.
        save (bool): Whether to keep the files saved.
        skip_decontamination (bool): Whether we run decontamination or not.
    """
    client = UploadAPIClient()

    batch_id, remote_batch_name, legacy_batch_id = create_batch_on_server(
        batch=batch,
        amplicon_scheme=batch.samples[0].amplicon_scheme,
    )

    upload_session = start_upload_session(
        batch_pk=batch_id, samples=batch.samples, api_client=client
    )

    upload_file_type = UploadData(
        access_token=env.get_access_token(env.get_host(None)),
        batch_pk=batch_id,
        env=env.get_upload_host(),
        samples=batch.samples,
        upload_session_id=upload_session.session_id,
    )

    mapping_csv_records = []

    for sample in upload_session.samples:
        for file in sample.files:
            mapping_csv_records.append(
                {
                    "batch_name": upload_session.name,
                    "pipeline_version": batch.pipeline_version,
                    "sample_name": file.prepared_file.name,
                    "remote_sample_name": file.sample_id,
                    "remote_batch_name": remote_batch_name,
                    "remote_batch_id": batch_id,
                }
            )

    util.write_csv(mapping_csv_records, f"{remote_batch_name}.mapping.csv")
    secho(
        f"The mapping file {remote_batch_name}.mapping.csv has been created.",
        fg="green",
    )
    secho(
        "You can monitor the progress of your batch in GPAS here: "
        + f"{env.get_protocol()}://{os.environ.get('GPAS_APP_HOST', DEFAULT_APP_HOST)}/batches/{legacy_batch_id}",
        fg="blue",
    )

    try:
        client.log_download_mapping_file_to_portal(
            str(legacy_batch_id),
            remote_batch_name,
        )
    except Exception:
        logger.warning("Could not log mapping-file download to portal")
        secho("Could not log mapping-file download to portal", fg="yellow")

    upload_samples(
        client=client, upload_data=upload_file_type, upload_session=upload_session
    )

    if not skip_decontamination and not save:
        for sample in upload_session.samples:
            for file in sample.files:
                if file.prepared_file.path:
                    remove_file(file_path=file.prepared_file.path)

    secho(
        f"Upload complete. Created {remote_batch_name}.mapping.csv (keep this safe)",
        fg="green",
    )


def get_pipeline_version(
    upload_client: UploadAPIClient, specimen_organism: str | None
) -> str | None:
    """Get the pipeline version for a given specimen organism.

    Args:
        upload_client (UploadAPIClient): The upload API client to use.
        specimen_organism (str | None): The specimen organism to get the pipeline version for.
    """
    latest_pipelines = upload_client.get_latest_pipelines()

    if not specimen_organism:
        return None

    for p in latest_pipelines:
        if p.get("name") == specimen_organism.lower():
            return p.get("version")

    return None


def get_pipeline_versions() -> list[PipelineVersion]:
    """Get a list of the latest pipeline versions."""
    upload_client = UploadAPIClient()
    latest_pipelines = upload_client.get_latest_pipelines()

    if not latest_pipelines:
        return []

    return latest_pipelines


def upload_samples(
    client: UploadAPIClient,
    upload_data: UploadData,
    upload_session: UploadSession,
) -> None:
    """Uploads samples once the upload session has been created.

    This function first prepares the files for upload, then uploads them in chunks
    using a thread pool executor for concurrent uploads. It finishes by ending the
    upload session.

    Args:
        client (UploadAPIClient): The upload API client to use.
        upload_data (UploadData): The upload data including batch_id, session info, etc.
        upload_session (UploadSession): The upload session including session id and samples.

    Returns:
        None
    """
    # upload the file chunks
    with ThreadPoolExecutor(max_workers=upload_data.max_concurrent_chunks) as executor:
        futures = []
        for sample in upload_session.samples:
            future = executor.submit(upload_sample, client, upload_data, sample)
            futures.append(future)

        # Need to tie halves of the samples together here
        # And call end session when all samples are uploaded
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error uploading sample: {e}")
                secho(f"Error uploading sample: {e}", fg="red", err=True)

    # end the upload session
    end_session = client.end_upload_session(
        upload_data.batch_pk, upload_session_id=upload_session.session_id
    )

    if end_session.status_code != 200:
        logger.error(f"Failed to end upload session for batch {upload_data.batch_pk}.")
        secho(
            f"Failed to end upload session for batch {upload_data.batch_pk}.",
            fg="red",
            err=True,
        )
    else:
        secho("All uploads complete.", bold=True, fg="green")


def upload_sample(
    client: UploadAPIClient,
    upload_data: UploadData,
    sample: Sample[UploadingFile],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Response:
    """Uploads files in a sample, chunk by chunk.

    Args:
        client (UploadAPIClient): The upload API client to use.
        upload_data (UploadData): The upload data including batch_id, session info, etc.
        sample (Sample[UploadingFile]): The sample to upload (with files, etc.)
        chunk_size (int): Default size of file chunk to upload (5mb)

    Returns:
        None: This function does not return anything, but calls the provided
            `on_progress` and `on_complete` callback functions.
    """
    with ThreadPoolExecutor(max_workers=upload_data.max_concurrent_chunks) as executor:
        futures = []
        for file in sample.files:
            future = executor.submit(upload_file, client, upload_data, file, chunk_size)
            futures.append(future)

        # Need to tie halves of the samples together here
        # And call end sample when a sample is finished uploading
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error uploading file: {e}")

    return client.end_sample_upload(
        upload_data.batch_pk,
        data={"upload_id": sample.files[0].upload_id},
    )


def upload_file(
    client: UploadAPIClient,
    upload_data: UploadData,
    file: UploadingFile,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> None:
    """Uploads chunks of a single file.

    Args:
        client (UploadAPIClient): The upload API client to use.
        upload_data (UploadData): The upload data including batch_id, session info, etc.
        file (SelectedFile): The file to upload (with file data, total chunks, etc.)
        chunk_size (int): Default size of file chunk to upload (5mb)

    Returns:
        None: This function does not return anything, but calls the provided
            `on_progress` and `on_complete` callback functions.
    """
    secho(f"Uploading {file.prepared_file.name}")
    logger.info(f"Uploading {file.prepared_file.name}")

    chunks_uploaded = 0
    chunk_queue: list[Response] = []
    total_chunks = ceil(file.prepared_file.size / chunk_size)
    if not file.prepared_file.path:
        return None
    with file.prepared_file.path.open("rb") as f:
        for i in range(total_chunks):  # total chunks = file.size/chunk_size
            process_queue(chunk_queue, upload_data.max_concurrent_chunks)

            # chunk the files
            file_chunk = f.read(chunk_size)
            if not file_chunk:
                break

            chunk_upload = client.upload_chunk(
                batch_pk=upload_data.batch_pk,
                protocol=env.get_protocol(),
                chunk=file_chunk,
                chunk_index=i,
                upload_id=file.upload_id,
            )
            chunk_queue.append(chunk_upload)
            try:
                chunk_upload_result = chunk_upload.json()

                # process result of chunk upload for upload chunks that don't return 400 status
                metrics = chunk_upload_result.get("metrics", {})
                if metrics:
                    chunks_uploaded += 1
                    progress = (chunks_uploaded / total_chunks) * 100

                    # Create an OnProgress instance
                    progress_event = OnProgress(
                        upload_id=file.upload_id,
                        batch_pk=upload_data.batch_pk,
                        progress=progress,
                        metrics=chunk_upload_result["metrics"],
                    )
                    upload_data.on_progress = progress_event

                # If all chunks have been uploaded, complete the file upload
                if chunks_uploaded == total_chunks:
                    complete_event = OnComplete(file.upload_id, upload_data.batch_pk)
                    upload_data.on_complete = complete_event
                    client = UploadAPIClient()
                    end_status = client.end_file_upload(
                        upload_data.batch_pk,
                        data={"upload_id": file.upload_id},
                    )
                    if end_status.status_code == 400:
                        logger.error(
                            f"Failed to end upload for file: {file.upload_id} (Batch ID: {upload_data.batch_pk})"
                        )

            except Exception as e:
                logger.error(
                    f"Error uploading chunk {i} for file: {file.upload_id} of batch {upload_data.batch_pk}: {str(e)}"
                )


def process_queue(chunk_queue: list, max_concurrent_chunks: int) -> Generator[Any]:
    """Processes a queue of chunks concurrently to ensure tno more than 'max_concurrent_chunks' are processed at the same time.

    Args:
        chunk_queue (list): A collection of futures (generated by thread pool executor)
        representing the chunks to be processed.
        max_concurrent_chunks (int): The maximum number of chunks to be processed concurrently.
    """
    if len(chunk_queue) >= max_concurrent_chunks:
        completed = []
        for future in as_completed(chunk_queue):
            yield future.result()
            completed.append(future)
        for future in completed:  # remove completed futures from queue
            chunk_queue.remove(future)


def start_upload_session(
    batch_pk: str,
    samples: list[models.UploadSample],
    api_client: UploadAPIClient,
) -> UploadSession:
    """Prepares multiple files for upload.

    This function starts the upload session,
    then starts the upload files for each file
    and returns the bundle.

    Args:
        batch_pk (str): The ID of the batch.
        samples (list[UploadSample]): List of samples to prepare the files for.
        api_client (UploadAPIClient): Instance of the APIClient class.

    Returns:
        UploadSession: Upload session id, name and samples.
    """
    batch_instrument_is_illumina = samples[0].is_illumina()

    prepared_samples: list[Sample[PreparedFile]] = [
        prepare_sample(sample) for sample in samples
    ]

    # Call start upload session endpoint
    upload_session_id, upload_session_name, sample_summaries = (
        api_client.start_upload_session(batch_pk, prepared_samples)
    )

    if batch_instrument_is_illumina:
        # Duplicate the summaries for each half of the files
        per_file_sample_summaries = [
            item for item in sample_summaries for _ in range(2)
        ]
    else:
        per_file_sample_summaries = sample_summaries

    # Call start upload file endpoint for each file
    index = 0
    uploading_samples: list[Sample[UploadingFile]] = []
    for unprepared_sample in prepared_samples:
        uploading_sample_files: list[UploadingFile] = []
        for file in unprepared_sample.files:
            sample_id = per_file_sample_summaries[index].get("sample_id")
            uploading_file = api_client.start_file_upload(
                file, batch_pk, sample_id, upload_session_id
            )
            uploading_sample_files.append(uploading_file)
            index += 1

        uploading_samples.append(
            Sample[UploadingFile](
                unprepared_sample.instrument_platform, uploading_sample_files
            )
        )

    # Return the bundle of start upload session and start file upload responses
    return UploadSession(
        session_id=upload_session_id,
        name=upload_session_name,
        samples=uploading_samples,
    )


def prepare_sample(sample: models.UploadSample) -> Sample[PreparedFile]:
    """Prepares a samples' file for upload.

    This function starts the upload session, checks the upload status of the current
    sample and if it has not already been uploaded or partially uploaded prepares
    the sample from scratch.

    Args:
        sample (UploadSample): The upload sample.

    Returns:
        SelectedSample: Prepared sample.
    """
    if sample.is_illumina():
        sample_files = [
            PreparedFile(upload_sample=sample, file_side=1),
            PreparedFile(upload_sample=sample, file_side=2),
        ]
    else:
        sample_files = [PreparedFile(upload_sample=sample, file_side=1)]

    return Sample[PreparedFile](
        instrument_platform=sample.instrument_platform, files=sample_files
    )


def remove_file(file_path: Path) -> None:
    """Remove a file from the filesystem.

    Args:
        file_path (Path): The path to the file to remove.
    """
    try:
        file_path.unlink()
        remove_empty_dir(file_path.parent)

    except OSError:
        logger.error(
            f"Failed to delete upload files created during execution, "
            f"files may still be in {file_path.parent}"
        )
        secho(
            "Failed to delete upload files created during execution, "
            + f"files may still be in {file_path.parent}",
            fg="red",
            err=True,
        )
    except Exception:
        pass  # A failure here doesn't matter since upload is complete


def remove_empty_dir(directory: Path):
    """Removes empty directory for the given path after upload is complete."""
    for _, _, files in os.walk(directory):
        if not files:
            directory.rmdir()
