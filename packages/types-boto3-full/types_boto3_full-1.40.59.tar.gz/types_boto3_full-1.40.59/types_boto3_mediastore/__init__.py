"""
Main interface for mediastore service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_mediastore/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_mediastore import (
        Client,
        ListContainersPaginator,
        MediaStoreClient,
    )

    session = Session()
    client: MediaStoreClient = session.client("mediastore")

    list_containers_paginator: ListContainersPaginator = client.get_paginator("list_containers")
    ```
"""

from .client import MediaStoreClient
from .paginator import ListContainersPaginator

Client = MediaStoreClient


__all__ = ("Client", "ListContainersPaginator", "MediaStoreClient")
