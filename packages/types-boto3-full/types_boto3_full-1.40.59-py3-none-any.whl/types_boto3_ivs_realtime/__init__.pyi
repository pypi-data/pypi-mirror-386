"""
Main interface for ivs-realtime service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_ivs_realtime/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_ivs_realtime import (
        Client,
        IvsrealtimeClient,
        ListIngestConfigurationsPaginator,
        ListParticipantReplicasPaginator,
        ListPublicKeysPaginator,
    )

    session = Session()
    client: IvsrealtimeClient = session.client("ivs-realtime")

    list_ingest_configurations_paginator: ListIngestConfigurationsPaginator = client.get_paginator("list_ingest_configurations")
    list_participant_replicas_paginator: ListParticipantReplicasPaginator = client.get_paginator("list_participant_replicas")
    list_public_keys_paginator: ListPublicKeysPaginator = client.get_paginator("list_public_keys")
    ```
"""

from .client import IvsrealtimeClient
from .paginator import (
    ListIngestConfigurationsPaginator,
    ListParticipantReplicasPaginator,
    ListPublicKeysPaginator,
)

Client = IvsrealtimeClient

__all__ = (
    "Client",
    "IvsrealtimeClient",
    "ListIngestConfigurationsPaginator",
    "ListParticipantReplicasPaginator",
    "ListPublicKeysPaginator",
)
