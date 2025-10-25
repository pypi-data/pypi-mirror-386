"""
Main interface for kinesis-video-webrtc-storage service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_kinesis_video_webrtc_storage/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_kinesis_video_webrtc_storage import (
        Client,
        KinesisVideoWebRTCStorageClient,
    )

    session = Session()
    client: KinesisVideoWebRTCStorageClient = session.client("kinesis-video-webrtc-storage")
    ```
"""

from .client import KinesisVideoWebRTCStorageClient

Client = KinesisVideoWebRTCStorageClient

__all__ = ("Client", "KinesisVideoWebRTCStorageClient")
