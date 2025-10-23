"""
Type annotations for bedrock-agentcore-control service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_bedrock_agentcore_control.client import BedrockAgentCoreControlPlaneFrontingLayerClient
    from types_boto3_bedrock_agentcore_control.paginator import (
        ListAgentRuntimeEndpointsPaginator,
        ListAgentRuntimeVersionsPaginator,
        ListAgentRuntimesPaginator,
        ListApiKeyCredentialProvidersPaginator,
        ListBrowsersPaginator,
        ListCodeInterpretersPaginator,
        ListGatewayTargetsPaginator,
        ListGatewaysPaginator,
        ListMemoriesPaginator,
        ListOauth2CredentialProvidersPaginator,
        ListWorkloadIdentitiesPaginator,
    )

    session = Session()
    client: BedrockAgentCoreControlPlaneFrontingLayerClient = session.client("bedrock-agentcore-control")

    list_agent_runtime_endpoints_paginator: ListAgentRuntimeEndpointsPaginator = client.get_paginator("list_agent_runtime_endpoints")
    list_agent_runtime_versions_paginator: ListAgentRuntimeVersionsPaginator = client.get_paginator("list_agent_runtime_versions")
    list_agent_runtimes_paginator: ListAgentRuntimesPaginator = client.get_paginator("list_agent_runtimes")
    list_api_key_credential_providers_paginator: ListApiKeyCredentialProvidersPaginator = client.get_paginator("list_api_key_credential_providers")
    list_browsers_paginator: ListBrowsersPaginator = client.get_paginator("list_browsers")
    list_code_interpreters_paginator: ListCodeInterpretersPaginator = client.get_paginator("list_code_interpreters")
    list_gateway_targets_paginator: ListGatewayTargetsPaginator = client.get_paginator("list_gateway_targets")
    list_gateways_paginator: ListGatewaysPaginator = client.get_paginator("list_gateways")
    list_memories_paginator: ListMemoriesPaginator = client.get_paginator("list_memories")
    list_oauth2_credential_providers_paginator: ListOauth2CredentialProvidersPaginator = client.get_paginator("list_oauth2_credential_providers")
    list_workload_identities_paginator: ListWorkloadIdentitiesPaginator = client.get_paginator("list_workload_identities")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    ListAgentRuntimeEndpointsRequestPaginateTypeDef,
    ListAgentRuntimeEndpointsResponseTypeDef,
    ListAgentRuntimesRequestPaginateTypeDef,
    ListAgentRuntimesResponseTypeDef,
    ListAgentRuntimeVersionsRequestPaginateTypeDef,
    ListAgentRuntimeVersionsResponseTypeDef,
    ListApiKeyCredentialProvidersRequestPaginateTypeDef,
    ListApiKeyCredentialProvidersResponseTypeDef,
    ListBrowsersRequestPaginateTypeDef,
    ListBrowsersResponseTypeDef,
    ListCodeInterpretersRequestPaginateTypeDef,
    ListCodeInterpretersResponseTypeDef,
    ListGatewaysRequestPaginateTypeDef,
    ListGatewaysResponseTypeDef,
    ListGatewayTargetsRequestPaginateTypeDef,
    ListGatewayTargetsResponseTypeDef,
    ListMemoriesInputPaginateTypeDef,
    ListMemoriesOutputTypeDef,
    ListOauth2CredentialProvidersRequestPaginateTypeDef,
    ListOauth2CredentialProvidersResponseTypeDef,
    ListWorkloadIdentitiesRequestPaginateTypeDef,
    ListWorkloadIdentitiesResponseTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack

__all__ = (
    "ListAgentRuntimeEndpointsPaginator",
    "ListAgentRuntimeVersionsPaginator",
    "ListAgentRuntimesPaginator",
    "ListApiKeyCredentialProvidersPaginator",
    "ListBrowsersPaginator",
    "ListCodeInterpretersPaginator",
    "ListGatewayTargetsPaginator",
    "ListGatewaysPaginator",
    "ListMemoriesPaginator",
    "ListOauth2CredentialProvidersPaginator",
    "ListWorkloadIdentitiesPaginator",
)

if TYPE_CHECKING:
    _ListAgentRuntimeEndpointsPaginatorBase = Paginator[ListAgentRuntimeEndpointsResponseTypeDef]
else:
    _ListAgentRuntimeEndpointsPaginatorBase = Paginator  # type: ignore[assignment]

class ListAgentRuntimeEndpointsPaginator(_ListAgentRuntimeEndpointsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimeEndpoints.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimeEndpoints)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimeendpointspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListAgentRuntimeEndpointsRequestPaginateTypeDef]
    ) -> PageIterator[ListAgentRuntimeEndpointsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimeEndpoints.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimeEndpoints.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimeendpointspaginator)
        """

if TYPE_CHECKING:
    _ListAgentRuntimeVersionsPaginatorBase = Paginator[ListAgentRuntimeVersionsResponseTypeDef]
else:
    _ListAgentRuntimeVersionsPaginatorBase = Paginator  # type: ignore[assignment]

class ListAgentRuntimeVersionsPaginator(_ListAgentRuntimeVersionsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimeVersions.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimeVersions)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimeversionspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListAgentRuntimeVersionsRequestPaginateTypeDef]
    ) -> PageIterator[ListAgentRuntimeVersionsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimeVersions.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimeVersions.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimeversionspaginator)
        """

if TYPE_CHECKING:
    _ListAgentRuntimesPaginatorBase = Paginator[ListAgentRuntimesResponseTypeDef]
else:
    _ListAgentRuntimesPaginatorBase = Paginator  # type: ignore[assignment]

class ListAgentRuntimesPaginator(_ListAgentRuntimesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimes.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimes)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListAgentRuntimesRequestPaginateTypeDef]
    ) -> PageIterator[ListAgentRuntimesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListAgentRuntimes.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListAgentRuntimes.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listagentruntimespaginator)
        """

if TYPE_CHECKING:
    _ListApiKeyCredentialProvidersPaginatorBase = Paginator[
        ListApiKeyCredentialProvidersResponseTypeDef
    ]
else:
    _ListApiKeyCredentialProvidersPaginatorBase = Paginator  # type: ignore[assignment]

class ListApiKeyCredentialProvidersPaginator(_ListApiKeyCredentialProvidersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListApiKeyCredentialProviders.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListApiKeyCredentialProviders)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listapikeycredentialproviderspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListApiKeyCredentialProvidersRequestPaginateTypeDef]
    ) -> PageIterator[ListApiKeyCredentialProvidersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListApiKeyCredentialProviders.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListApiKeyCredentialProviders.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listapikeycredentialproviderspaginator)
        """

if TYPE_CHECKING:
    _ListBrowsersPaginatorBase = Paginator[ListBrowsersResponseTypeDef]
else:
    _ListBrowsersPaginatorBase = Paginator  # type: ignore[assignment]

class ListBrowsersPaginator(_ListBrowsersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListBrowsers.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListBrowsers)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listbrowserspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListBrowsersRequestPaginateTypeDef]
    ) -> PageIterator[ListBrowsersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListBrowsers.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListBrowsers.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listbrowserspaginator)
        """

if TYPE_CHECKING:
    _ListCodeInterpretersPaginatorBase = Paginator[ListCodeInterpretersResponseTypeDef]
else:
    _ListCodeInterpretersPaginatorBase = Paginator  # type: ignore[assignment]

class ListCodeInterpretersPaginator(_ListCodeInterpretersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListCodeInterpreters.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListCodeInterpreters)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listcodeinterpreterspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListCodeInterpretersRequestPaginateTypeDef]
    ) -> PageIterator[ListCodeInterpretersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListCodeInterpreters.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListCodeInterpreters.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listcodeinterpreterspaginator)
        """

if TYPE_CHECKING:
    _ListGatewayTargetsPaginatorBase = Paginator[ListGatewayTargetsResponseTypeDef]
else:
    _ListGatewayTargetsPaginatorBase = Paginator  # type: ignore[assignment]

class ListGatewayTargetsPaginator(_ListGatewayTargetsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListGatewayTargets.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListGatewayTargets)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listgatewaytargetspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListGatewayTargetsRequestPaginateTypeDef]
    ) -> PageIterator[ListGatewayTargetsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListGatewayTargets.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListGatewayTargets.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listgatewaytargetspaginator)
        """

if TYPE_CHECKING:
    _ListGatewaysPaginatorBase = Paginator[ListGatewaysResponseTypeDef]
else:
    _ListGatewaysPaginatorBase = Paginator  # type: ignore[assignment]

class ListGatewaysPaginator(_ListGatewaysPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListGateways.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListGateways)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listgatewayspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListGatewaysRequestPaginateTypeDef]
    ) -> PageIterator[ListGatewaysResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListGateways.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListGateways.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listgatewayspaginator)
        """

if TYPE_CHECKING:
    _ListMemoriesPaginatorBase = Paginator[ListMemoriesOutputTypeDef]
else:
    _ListMemoriesPaginatorBase = Paginator  # type: ignore[assignment]

class ListMemoriesPaginator(_ListMemoriesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListMemories.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListMemories)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listmemoriespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListMemoriesInputPaginateTypeDef]
    ) -> PageIterator[ListMemoriesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListMemories.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListMemories.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listmemoriespaginator)
        """

if TYPE_CHECKING:
    _ListOauth2CredentialProvidersPaginatorBase = Paginator[
        ListOauth2CredentialProvidersResponseTypeDef
    ]
else:
    _ListOauth2CredentialProvidersPaginatorBase = Paginator  # type: ignore[assignment]

class ListOauth2CredentialProvidersPaginator(_ListOauth2CredentialProvidersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListOauth2CredentialProviders.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListOauth2CredentialProviders)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listoauth2credentialproviderspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListOauth2CredentialProvidersRequestPaginateTypeDef]
    ) -> PageIterator[ListOauth2CredentialProvidersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListOauth2CredentialProviders.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListOauth2CredentialProviders.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listoauth2credentialproviderspaginator)
        """

if TYPE_CHECKING:
    _ListWorkloadIdentitiesPaginatorBase = Paginator[ListWorkloadIdentitiesResponseTypeDef]
else:
    _ListWorkloadIdentitiesPaginatorBase = Paginator  # type: ignore[assignment]

class ListWorkloadIdentitiesPaginator(_ListWorkloadIdentitiesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListWorkloadIdentities.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListWorkloadIdentities)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listworkloadidentitiespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListWorkloadIdentitiesRequestPaginateTypeDef]
    ) -> PageIterator[ListWorkloadIdentitiesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/paginator/ListWorkloadIdentities.html#BedrockAgentCoreControlPlaneFrontingLayer.Paginator.ListWorkloadIdentities.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agentcore_control/paginators/#listworkloadidentitiespaginator)
        """
