# Copyright 2024 Luminary Cloud, Inc. All Rights Reserved.
from os import PathLike
import os
import pathlib
from typing import Mapping
from urllib.parse import urlparse
import requests
import logging
import grpc

from . import util
from .._client import Client
from luminarycloud._proto.upload import upload_pb2 as uploadpb

logger = logging.getLogger(__name__)


def gcs_resumable_upload(
    client: Client, filepath: PathLike | str, signed_url: str, http_headers: Mapping[str, str]
) -> None:
    """
    Performs a resumable upload to a GCS signed url.
    Based on: https://cloud.google.com/storage/docs/performing-resumable-uploads
    TODO(LC-19950): add retries and multi-chunk uploads (https://cloud.google.com/storage/docs/performing-resumable-uploads#chunked-upload)
    """

    # initiate the upload
    parsed_url = urlparse(signed_url)
    try:
        if parsed_url.hostname and parsed_url.hostname.endswith(".luminarycloud.com"):
            # we must be using the gcsproxy, so we'll use the `client.http` client to authenticate
            # with our backend
            logger.debug("signed url points to LC backend, will use authenticated client")
            post_res = client.http.raw_request("POST", signed_url, headers=http_headers)
        else:
            # we're using the GCS signed url directly, no additional authentication is needed
            logger.debug("signed url points to GCS, will use unauthenticated client")
            post_res = requests.post(url=signed_url, headers=http_headers)
        logger.debug(
            f"sucessfully initialized signed URL upload for {filepath}, POST status code: {post_res.status_code}"
        )
    except:
        # don't log the signed_url, just to be safe
        msg = (
            f"failed to initialize signed URL upload for {filepath}, POST status code: {post_res.status_code}, content: "
            + str(post_res.content)
        )
        logger.error(msg)
        raise Exception(msg)

    # upload the file
    try:
        # we need to grab the session_uri from the response; this will be the URL we
        # use to actually PUT the data
        session_uri = post_res.headers["Location"]
        size = os.path.getsize(filepath)
        with open(filepath, "rb") as fp:
            # even if a signed url upload is initiated via the gcsproxy, the subsequent PUT request
            # goes straight to GCS, so we don't want to use the authenticated client here
            put_res = requests.put(
                url=session_uri,
                headers={
                    "content-length": str(size),
                },
                data=fp.read(size),
            )
            logger.debug(f"sucessfully uploaded {filepath}, PUT status code: {put_res.status_code}")
    except Exception as e:
        # don't log the session_uri, just to be safe
        msg = f"failed to upload {filepath}, {e})"
        logger.error(msg)
        raise Exception(e)


def upload_file(
    client: Client,
    project_id: str,
    resource_params: uploadpb.ResourceParams,
    file_path: PathLike | str,
) -> tuple[str, uploadpb.FinishUploadReply]:
    file_metadata = util.get_file_metadata(pathlib.Path(file_path))

    create_upload_res: uploadpb.CreateUploadReply = client.CreateUpload(
        uploadpb.CreateUploadRequest(
            project_id=project_id,
            file_meta=file_metadata,
            resource_params=resource_params,
        )
    )
    upload_id = create_upload_res.upload.id
    logger.debug(f"created upload: {upload_id}")

    try:
        start_res = client.StartUpload(
            uploadpb.StartUploadRequest(upload_id=upload_id, method=uploadpb.METHOD_GCS_RESUMABLE)
        )
        logger.debug("started gcs upload")

        gcs_resumable_upload(
            client=client,
            filepath=pathlib.Path(file_path),
            signed_url=start_res.upload.gcs_resumable.signed_url,
            http_headers=start_res.upload.gcs_resumable.http_headers,
        )
        logger.debug("successfully uploaded gcs data")
    except grpc.RpcError as e:
        if e.code() != grpc.StatusCode.UNIMPLEMENTED:
            raise e
        start_res = client.StartUpload(
            uploadpb.StartUploadRequest(upload_id=upload_id, method=uploadpb.METHOD_SIMPLE)
        )
        logger.debug("started simple upload")

        # Simple non-chunked upload
        with open(file_path, "rb") as fp:
            client.UploadData(
                uploadpb.UploadDataRequest(
                    upload_id=upload_id,
                    offset=0,
                    data=fp.read(),
                )
            )
        logger.debug("successfully uploaded simple data")

    finish_res: uploadpb.FinishUploadReply = client.FinishUpload(
        uploadpb.FinishUploadRequest(upload_id=upload_id)
    )
    logger.debug("finished upload")

    return upload_id, finish_res
