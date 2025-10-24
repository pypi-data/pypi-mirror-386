"""
Main interface for connectcampaigns service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_connectcampaigns/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_connectcampaigns import (
        Client,
        ConnectCampaignServiceClient,
        ListCampaignsPaginator,
    )

    session = Session()
    client: ConnectCampaignServiceClient = session.client("connectcampaigns")

    list_campaigns_paginator: ListCampaignsPaginator = client.get_paginator("list_campaigns")
    ```
"""

from .client import ConnectCampaignServiceClient
from .paginator import ListCampaignsPaginator

Client = ConnectCampaignServiceClient

__all__ = ("Client", "ConnectCampaignServiceClient", "ListCampaignsPaginator")
