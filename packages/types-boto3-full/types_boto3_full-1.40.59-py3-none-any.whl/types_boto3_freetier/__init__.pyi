"""
Main interface for freetier service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_freetier/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_freetier import (
        Client,
        FreeTierClient,
        GetFreeTierUsagePaginator,
        ListAccountActivitiesPaginator,
    )

    session = Session()
    client: FreeTierClient = session.client("freetier")

    get_free_tier_usage_paginator: GetFreeTierUsagePaginator = client.get_paginator("get_free_tier_usage")
    list_account_activities_paginator: ListAccountActivitiesPaginator = client.get_paginator("list_account_activities")
    ```
"""

from .client import FreeTierClient
from .paginator import GetFreeTierUsagePaginator, ListAccountActivitiesPaginator

Client = FreeTierClient

__all__ = (
    "Client",
    "FreeTierClient",
    "GetFreeTierUsagePaginator",
    "ListAccountActivitiesPaginator",
)
