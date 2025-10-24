"""
Main interface for translate service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_translate/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_translate import (
        Client,
        ListTerminologiesPaginator,
        TranslateClient,
    )

    session = Session()
    client: TranslateClient = session.client("translate")

    list_terminologies_paginator: ListTerminologiesPaginator = client.get_paginator("list_terminologies")
    ```
"""

from .client import TranslateClient
from .paginator import ListTerminologiesPaginator

Client = TranslateClient

__all__ = ("Client", "ListTerminologiesPaginator", "TranslateClient")
