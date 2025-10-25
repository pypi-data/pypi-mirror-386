"""
Main interface for resourcegroupstaggingapi service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_resourcegroupstaggingapi/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_resourcegroupstaggingapi import (
        Client,
        GetComplianceSummaryPaginator,
        GetResourcesPaginator,
        GetTagKeysPaginator,
        GetTagValuesPaginator,
        ResourceGroupsTaggingAPIClient,
    )

    session = Session()
    client: ResourceGroupsTaggingAPIClient = session.client("resourcegroupstaggingapi")

    get_compliance_summary_paginator: GetComplianceSummaryPaginator = client.get_paginator("get_compliance_summary")
    get_resources_paginator: GetResourcesPaginator = client.get_paginator("get_resources")
    get_tag_keys_paginator: GetTagKeysPaginator = client.get_paginator("get_tag_keys")
    get_tag_values_paginator: GetTagValuesPaginator = client.get_paginator("get_tag_values")
    ```
"""

from .client import ResourceGroupsTaggingAPIClient
from .paginator import (
    GetComplianceSummaryPaginator,
    GetResourcesPaginator,
    GetTagKeysPaginator,
    GetTagValuesPaginator,
)

Client = ResourceGroupsTaggingAPIClient


__all__ = (
    "Client",
    "GetComplianceSummaryPaginator",
    "GetResourcesPaginator",
    "GetTagKeysPaginator",
    "GetTagValuesPaginator",
    "ResourceGroupsTaggingAPIClient",
)
