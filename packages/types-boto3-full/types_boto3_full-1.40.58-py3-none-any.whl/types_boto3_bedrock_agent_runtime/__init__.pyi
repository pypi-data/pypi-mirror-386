"""
Main interface for bedrock-agent-runtime service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agent_runtime/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_bedrock_agent_runtime import (
        AgentsforBedrockRuntimeClient,
        Client,
        GetAgentMemoryPaginator,
        ListFlowExecutionEventsPaginator,
        ListFlowExecutionsPaginator,
        ListInvocationStepsPaginator,
        ListInvocationsPaginator,
        ListSessionsPaginator,
        RerankPaginator,
        RetrievePaginator,
    )

    session = Session()
    client: AgentsforBedrockRuntimeClient = session.client("bedrock-agent-runtime")

    get_agent_memory_paginator: GetAgentMemoryPaginator = client.get_paginator("get_agent_memory")
    list_flow_execution_events_paginator: ListFlowExecutionEventsPaginator = client.get_paginator("list_flow_execution_events")
    list_flow_executions_paginator: ListFlowExecutionsPaginator = client.get_paginator("list_flow_executions")
    list_invocation_steps_paginator: ListInvocationStepsPaginator = client.get_paginator("list_invocation_steps")
    list_invocations_paginator: ListInvocationsPaginator = client.get_paginator("list_invocations")
    list_sessions_paginator: ListSessionsPaginator = client.get_paginator("list_sessions")
    rerank_paginator: RerankPaginator = client.get_paginator("rerank")
    retrieve_paginator: RetrievePaginator = client.get_paginator("retrieve")
    ```
"""

from .client import AgentsforBedrockRuntimeClient
from .paginator import (
    GetAgentMemoryPaginator,
    ListFlowExecutionEventsPaginator,
    ListFlowExecutionsPaginator,
    ListInvocationsPaginator,
    ListInvocationStepsPaginator,
    ListSessionsPaginator,
    RerankPaginator,
    RetrievePaginator,
)

Client = AgentsforBedrockRuntimeClient

__all__ = (
    "AgentsforBedrockRuntimeClient",
    "Client",
    "GetAgentMemoryPaginator",
    "ListFlowExecutionEventsPaginator",
    "ListFlowExecutionsPaginator",
    "ListInvocationStepsPaginator",
    "ListInvocationsPaginator",
    "ListSessionsPaginator",
    "RerankPaginator",
    "RetrievePaginator",
)
