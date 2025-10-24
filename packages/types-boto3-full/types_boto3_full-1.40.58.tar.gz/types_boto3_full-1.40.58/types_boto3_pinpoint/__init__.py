"""
Main interface for pinpoint service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_pinpoint/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_pinpoint import (
        Client,
        PinpointClient,
    )

    session = Session()
    client: PinpointClient = session.client("pinpoint")
    ```
"""

from .client import PinpointClient

Client = PinpointClient


__all__ = ("Client", "PinpointClient")
