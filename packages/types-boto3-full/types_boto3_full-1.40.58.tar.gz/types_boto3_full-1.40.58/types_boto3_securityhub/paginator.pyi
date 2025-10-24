"""
Type annotations for securityhub service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_securityhub.client import SecurityHubClient
    from types_boto3_securityhub.paginator import (
        DescribeActionTargetsPaginator,
        DescribeProductsPaginator,
        DescribeProductsV2Paginator,
        DescribeStandardsControlsPaginator,
        DescribeStandardsPaginator,
        GetEnabledStandardsPaginator,
        GetFindingHistoryPaginator,
        GetFindingsPaginator,
        GetFindingsV2Paginator,
        GetInsightsPaginator,
        GetResourcesV2Paginator,
        ListAggregatorsV2Paginator,
        ListConfigurationPoliciesPaginator,
        ListConfigurationPolicyAssociationsPaginator,
        ListEnabledProductsForImportPaginator,
        ListFindingAggregatorsPaginator,
        ListInvitationsPaginator,
        ListMembersPaginator,
        ListOrganizationAdminAccountsPaginator,
        ListSecurityControlDefinitionsPaginator,
        ListStandardsControlAssociationsPaginator,
    )

    session = Session()
    client: SecurityHubClient = session.client("securityhub")

    describe_action_targets_paginator: DescribeActionTargetsPaginator = client.get_paginator("describe_action_targets")
    describe_products_paginator: DescribeProductsPaginator = client.get_paginator("describe_products")
    describe_products_v2_paginator: DescribeProductsV2Paginator = client.get_paginator("describe_products_v2")
    describe_standards_controls_paginator: DescribeStandardsControlsPaginator = client.get_paginator("describe_standards_controls")
    describe_standards_paginator: DescribeStandardsPaginator = client.get_paginator("describe_standards")
    get_enabled_standards_paginator: GetEnabledStandardsPaginator = client.get_paginator("get_enabled_standards")
    get_finding_history_paginator: GetFindingHistoryPaginator = client.get_paginator("get_finding_history")
    get_findings_paginator: GetFindingsPaginator = client.get_paginator("get_findings")
    get_findings_v2_paginator: GetFindingsV2Paginator = client.get_paginator("get_findings_v2")
    get_insights_paginator: GetInsightsPaginator = client.get_paginator("get_insights")
    get_resources_v2_paginator: GetResourcesV2Paginator = client.get_paginator("get_resources_v2")
    list_aggregators_v2_paginator: ListAggregatorsV2Paginator = client.get_paginator("list_aggregators_v2")
    list_configuration_policies_paginator: ListConfigurationPoliciesPaginator = client.get_paginator("list_configuration_policies")
    list_configuration_policy_associations_paginator: ListConfigurationPolicyAssociationsPaginator = client.get_paginator("list_configuration_policy_associations")
    list_enabled_products_for_import_paginator: ListEnabledProductsForImportPaginator = client.get_paginator("list_enabled_products_for_import")
    list_finding_aggregators_paginator: ListFindingAggregatorsPaginator = client.get_paginator("list_finding_aggregators")
    list_invitations_paginator: ListInvitationsPaginator = client.get_paginator("list_invitations")
    list_members_paginator: ListMembersPaginator = client.get_paginator("list_members")
    list_organization_admin_accounts_paginator: ListOrganizationAdminAccountsPaginator = client.get_paginator("list_organization_admin_accounts")
    list_security_control_definitions_paginator: ListSecurityControlDefinitionsPaginator = client.get_paginator("list_security_control_definitions")
    list_standards_control_associations_paginator: ListStandardsControlAssociationsPaginator = client.get_paginator("list_standards_control_associations")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    DescribeActionTargetsRequestPaginateTypeDef,
    DescribeActionTargetsResponseTypeDef,
    DescribeProductsRequestPaginateTypeDef,
    DescribeProductsResponseTypeDef,
    DescribeProductsV2RequestPaginateTypeDef,
    DescribeProductsV2ResponseTypeDef,
    DescribeStandardsControlsRequestPaginateTypeDef,
    DescribeStandardsControlsResponseTypeDef,
    DescribeStandardsRequestPaginateTypeDef,
    DescribeStandardsResponseTypeDef,
    GetEnabledStandardsRequestPaginateTypeDef,
    GetEnabledStandardsResponseTypeDef,
    GetFindingHistoryRequestPaginateTypeDef,
    GetFindingHistoryResponseTypeDef,
    GetFindingsRequestPaginateTypeDef,
    GetFindingsResponseTypeDef,
    GetFindingsV2RequestPaginateTypeDef,
    GetFindingsV2ResponseTypeDef,
    GetInsightsRequestPaginateTypeDef,
    GetInsightsResponseTypeDef,
    GetResourcesV2RequestPaginateTypeDef,
    GetResourcesV2ResponseTypeDef,
    ListAggregatorsV2RequestPaginateTypeDef,
    ListAggregatorsV2ResponseTypeDef,
    ListConfigurationPoliciesRequestPaginateTypeDef,
    ListConfigurationPoliciesResponseTypeDef,
    ListConfigurationPolicyAssociationsRequestPaginateTypeDef,
    ListConfigurationPolicyAssociationsResponseTypeDef,
    ListEnabledProductsForImportRequestPaginateTypeDef,
    ListEnabledProductsForImportResponseTypeDef,
    ListFindingAggregatorsRequestPaginateTypeDef,
    ListFindingAggregatorsResponseTypeDef,
    ListInvitationsRequestPaginateTypeDef,
    ListInvitationsResponseTypeDef,
    ListMembersRequestPaginateTypeDef,
    ListMembersResponseTypeDef,
    ListOrganizationAdminAccountsRequestPaginateTypeDef,
    ListOrganizationAdminAccountsResponseTypeDef,
    ListSecurityControlDefinitionsRequestPaginateTypeDef,
    ListSecurityControlDefinitionsResponseTypeDef,
    ListStandardsControlAssociationsRequestPaginateTypeDef,
    ListStandardsControlAssociationsResponseTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack

__all__ = (
    "DescribeActionTargetsPaginator",
    "DescribeProductsPaginator",
    "DescribeProductsV2Paginator",
    "DescribeStandardsControlsPaginator",
    "DescribeStandardsPaginator",
    "GetEnabledStandardsPaginator",
    "GetFindingHistoryPaginator",
    "GetFindingsPaginator",
    "GetFindingsV2Paginator",
    "GetInsightsPaginator",
    "GetResourcesV2Paginator",
    "ListAggregatorsV2Paginator",
    "ListConfigurationPoliciesPaginator",
    "ListConfigurationPolicyAssociationsPaginator",
    "ListEnabledProductsForImportPaginator",
    "ListFindingAggregatorsPaginator",
    "ListInvitationsPaginator",
    "ListMembersPaginator",
    "ListOrganizationAdminAccountsPaginator",
    "ListSecurityControlDefinitionsPaginator",
    "ListStandardsControlAssociationsPaginator",
)

if TYPE_CHECKING:
    _DescribeActionTargetsPaginatorBase = Paginator[DescribeActionTargetsResponseTypeDef]
else:
    _DescribeActionTargetsPaginatorBase = Paginator  # type: ignore[assignment]

class DescribeActionTargetsPaginator(_DescribeActionTargetsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeActionTargets.html#SecurityHub.Paginator.DescribeActionTargets)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeactiontargetspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeActionTargetsRequestPaginateTypeDef]
    ) -> PageIterator[DescribeActionTargetsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeActionTargets.html#SecurityHub.Paginator.DescribeActionTargets.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeactiontargetspaginator)
        """

if TYPE_CHECKING:
    _DescribeProductsPaginatorBase = Paginator[DescribeProductsResponseTypeDef]
else:
    _DescribeProductsPaginatorBase = Paginator  # type: ignore[assignment]

class DescribeProductsPaginator(_DescribeProductsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeProducts.html#SecurityHub.Paginator.DescribeProducts)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeproductspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeProductsRequestPaginateTypeDef]
    ) -> PageIterator[DescribeProductsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeProducts.html#SecurityHub.Paginator.DescribeProducts.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeproductspaginator)
        """

if TYPE_CHECKING:
    _DescribeProductsV2PaginatorBase = Paginator[DescribeProductsV2ResponseTypeDef]
else:
    _DescribeProductsV2PaginatorBase = Paginator  # type: ignore[assignment]

class DescribeProductsV2Paginator(_DescribeProductsV2PaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeProductsV2.html#SecurityHub.Paginator.DescribeProductsV2)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeproductsv2paginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeProductsV2RequestPaginateTypeDef]
    ) -> PageIterator[DescribeProductsV2ResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeProductsV2.html#SecurityHub.Paginator.DescribeProductsV2.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describeproductsv2paginator)
        """

if TYPE_CHECKING:
    _DescribeStandardsControlsPaginatorBase = Paginator[DescribeStandardsControlsResponseTypeDef]
else:
    _DescribeStandardsControlsPaginatorBase = Paginator  # type: ignore[assignment]

class DescribeStandardsControlsPaginator(_DescribeStandardsControlsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeStandardsControls.html#SecurityHub.Paginator.DescribeStandardsControls)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describestandardscontrolspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeStandardsControlsRequestPaginateTypeDef]
    ) -> PageIterator[DescribeStandardsControlsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeStandardsControls.html#SecurityHub.Paginator.DescribeStandardsControls.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describestandardscontrolspaginator)
        """

if TYPE_CHECKING:
    _DescribeStandardsPaginatorBase = Paginator[DescribeStandardsResponseTypeDef]
else:
    _DescribeStandardsPaginatorBase = Paginator  # type: ignore[assignment]

class DescribeStandardsPaginator(_DescribeStandardsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeStandards.html#SecurityHub.Paginator.DescribeStandards)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describestandardspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeStandardsRequestPaginateTypeDef]
    ) -> PageIterator[DescribeStandardsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/DescribeStandards.html#SecurityHub.Paginator.DescribeStandards.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#describestandardspaginator)
        """

if TYPE_CHECKING:
    _GetEnabledStandardsPaginatorBase = Paginator[GetEnabledStandardsResponseTypeDef]
else:
    _GetEnabledStandardsPaginatorBase = Paginator  # type: ignore[assignment]

class GetEnabledStandardsPaginator(_GetEnabledStandardsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetEnabledStandards.html#SecurityHub.Paginator.GetEnabledStandards)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getenabledstandardspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetEnabledStandardsRequestPaginateTypeDef]
    ) -> PageIterator[GetEnabledStandardsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetEnabledStandards.html#SecurityHub.Paginator.GetEnabledStandards.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getenabledstandardspaginator)
        """

if TYPE_CHECKING:
    _GetFindingHistoryPaginatorBase = Paginator[GetFindingHistoryResponseTypeDef]
else:
    _GetFindingHistoryPaginatorBase = Paginator  # type: ignore[assignment]

class GetFindingHistoryPaginator(_GetFindingHistoryPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindingHistory.html#SecurityHub.Paginator.GetFindingHistory)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindinghistorypaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetFindingHistoryRequestPaginateTypeDef]
    ) -> PageIterator[GetFindingHistoryResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindingHistory.html#SecurityHub.Paginator.GetFindingHistory.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindinghistorypaginator)
        """

if TYPE_CHECKING:
    _GetFindingsPaginatorBase = Paginator[GetFindingsResponseTypeDef]
else:
    _GetFindingsPaginatorBase = Paginator  # type: ignore[assignment]

class GetFindingsPaginator(_GetFindingsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindings.html#SecurityHub.Paginator.GetFindings)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindingspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetFindingsRequestPaginateTypeDef]
    ) -> PageIterator[GetFindingsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindings.html#SecurityHub.Paginator.GetFindings.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindingspaginator)
        """

if TYPE_CHECKING:
    _GetFindingsV2PaginatorBase = Paginator[GetFindingsV2ResponseTypeDef]
else:
    _GetFindingsV2PaginatorBase = Paginator  # type: ignore[assignment]

class GetFindingsV2Paginator(_GetFindingsV2PaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindingsV2.html#SecurityHub.Paginator.GetFindingsV2)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindingsv2paginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetFindingsV2RequestPaginateTypeDef]
    ) -> PageIterator[GetFindingsV2ResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetFindingsV2.html#SecurityHub.Paginator.GetFindingsV2.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getfindingsv2paginator)
        """

if TYPE_CHECKING:
    _GetInsightsPaginatorBase = Paginator[GetInsightsResponseTypeDef]
else:
    _GetInsightsPaginatorBase = Paginator  # type: ignore[assignment]

class GetInsightsPaginator(_GetInsightsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetInsights.html#SecurityHub.Paginator.GetInsights)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getinsightspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetInsightsRequestPaginateTypeDef]
    ) -> PageIterator[GetInsightsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetInsights.html#SecurityHub.Paginator.GetInsights.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getinsightspaginator)
        """

if TYPE_CHECKING:
    _GetResourcesV2PaginatorBase = Paginator[GetResourcesV2ResponseTypeDef]
else:
    _GetResourcesV2PaginatorBase = Paginator  # type: ignore[assignment]

class GetResourcesV2Paginator(_GetResourcesV2PaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetResourcesV2.html#SecurityHub.Paginator.GetResourcesV2)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getresourcesv2paginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[GetResourcesV2RequestPaginateTypeDef]
    ) -> PageIterator[GetResourcesV2ResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/GetResourcesV2.html#SecurityHub.Paginator.GetResourcesV2.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#getresourcesv2paginator)
        """

if TYPE_CHECKING:
    _ListAggregatorsV2PaginatorBase = Paginator[ListAggregatorsV2ResponseTypeDef]
else:
    _ListAggregatorsV2PaginatorBase = Paginator  # type: ignore[assignment]

class ListAggregatorsV2Paginator(_ListAggregatorsV2PaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListAggregatorsV2.html#SecurityHub.Paginator.ListAggregatorsV2)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listaggregatorsv2paginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListAggregatorsV2RequestPaginateTypeDef]
    ) -> PageIterator[ListAggregatorsV2ResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListAggregatorsV2.html#SecurityHub.Paginator.ListAggregatorsV2.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listaggregatorsv2paginator)
        """

if TYPE_CHECKING:
    _ListConfigurationPoliciesPaginatorBase = Paginator[ListConfigurationPoliciesResponseTypeDef]
else:
    _ListConfigurationPoliciesPaginatorBase = Paginator  # type: ignore[assignment]

class ListConfigurationPoliciesPaginator(_ListConfigurationPoliciesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListConfigurationPolicies.html#SecurityHub.Paginator.ListConfigurationPolicies)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listconfigurationpoliciespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListConfigurationPoliciesRequestPaginateTypeDef]
    ) -> PageIterator[ListConfigurationPoliciesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListConfigurationPolicies.html#SecurityHub.Paginator.ListConfigurationPolicies.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listconfigurationpoliciespaginator)
        """

if TYPE_CHECKING:
    _ListConfigurationPolicyAssociationsPaginatorBase = Paginator[
        ListConfigurationPolicyAssociationsResponseTypeDef
    ]
else:
    _ListConfigurationPolicyAssociationsPaginatorBase = Paginator  # type: ignore[assignment]

class ListConfigurationPolicyAssociationsPaginator(
    _ListConfigurationPolicyAssociationsPaginatorBase
):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListConfigurationPolicyAssociations.html#SecurityHub.Paginator.ListConfigurationPolicyAssociations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listconfigurationpolicyassociationspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListConfigurationPolicyAssociationsRequestPaginateTypeDef]
    ) -> PageIterator[ListConfigurationPolicyAssociationsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListConfigurationPolicyAssociations.html#SecurityHub.Paginator.ListConfigurationPolicyAssociations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listconfigurationpolicyassociationspaginator)
        """

if TYPE_CHECKING:
    _ListEnabledProductsForImportPaginatorBase = Paginator[
        ListEnabledProductsForImportResponseTypeDef
    ]
else:
    _ListEnabledProductsForImportPaginatorBase = Paginator  # type: ignore[assignment]

class ListEnabledProductsForImportPaginator(_ListEnabledProductsForImportPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListEnabledProductsForImport.html#SecurityHub.Paginator.ListEnabledProductsForImport)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listenabledproductsforimportpaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListEnabledProductsForImportRequestPaginateTypeDef]
    ) -> PageIterator[ListEnabledProductsForImportResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListEnabledProductsForImport.html#SecurityHub.Paginator.ListEnabledProductsForImport.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listenabledproductsforimportpaginator)
        """

if TYPE_CHECKING:
    _ListFindingAggregatorsPaginatorBase = Paginator[ListFindingAggregatorsResponseTypeDef]
else:
    _ListFindingAggregatorsPaginatorBase = Paginator  # type: ignore[assignment]

class ListFindingAggregatorsPaginator(_ListFindingAggregatorsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListFindingAggregators.html#SecurityHub.Paginator.ListFindingAggregators)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listfindingaggregatorspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListFindingAggregatorsRequestPaginateTypeDef]
    ) -> PageIterator[ListFindingAggregatorsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListFindingAggregators.html#SecurityHub.Paginator.ListFindingAggregators.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listfindingaggregatorspaginator)
        """

if TYPE_CHECKING:
    _ListInvitationsPaginatorBase = Paginator[ListInvitationsResponseTypeDef]
else:
    _ListInvitationsPaginatorBase = Paginator  # type: ignore[assignment]

class ListInvitationsPaginator(_ListInvitationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListInvitations.html#SecurityHub.Paginator.ListInvitations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listinvitationspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListInvitationsRequestPaginateTypeDef]
    ) -> PageIterator[ListInvitationsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListInvitations.html#SecurityHub.Paginator.ListInvitations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listinvitationspaginator)
        """

if TYPE_CHECKING:
    _ListMembersPaginatorBase = Paginator[ListMembersResponseTypeDef]
else:
    _ListMembersPaginatorBase = Paginator  # type: ignore[assignment]

class ListMembersPaginator(_ListMembersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListMembers.html#SecurityHub.Paginator.ListMembers)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listmemberspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListMembersRequestPaginateTypeDef]
    ) -> PageIterator[ListMembersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListMembers.html#SecurityHub.Paginator.ListMembers.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listmemberspaginator)
        """

if TYPE_CHECKING:
    _ListOrganizationAdminAccountsPaginatorBase = Paginator[
        ListOrganizationAdminAccountsResponseTypeDef
    ]
else:
    _ListOrganizationAdminAccountsPaginatorBase = Paginator  # type: ignore[assignment]

class ListOrganizationAdminAccountsPaginator(_ListOrganizationAdminAccountsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListOrganizationAdminAccounts.html#SecurityHub.Paginator.ListOrganizationAdminAccounts)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listorganizationadminaccountspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListOrganizationAdminAccountsRequestPaginateTypeDef]
    ) -> PageIterator[ListOrganizationAdminAccountsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListOrganizationAdminAccounts.html#SecurityHub.Paginator.ListOrganizationAdminAccounts.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listorganizationadminaccountspaginator)
        """

if TYPE_CHECKING:
    _ListSecurityControlDefinitionsPaginatorBase = Paginator[
        ListSecurityControlDefinitionsResponseTypeDef
    ]
else:
    _ListSecurityControlDefinitionsPaginatorBase = Paginator  # type: ignore[assignment]

class ListSecurityControlDefinitionsPaginator(_ListSecurityControlDefinitionsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListSecurityControlDefinitions.html#SecurityHub.Paginator.ListSecurityControlDefinitions)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listsecuritycontroldefinitionspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListSecurityControlDefinitionsRequestPaginateTypeDef]
    ) -> PageIterator[ListSecurityControlDefinitionsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListSecurityControlDefinitions.html#SecurityHub.Paginator.ListSecurityControlDefinitions.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#listsecuritycontroldefinitionspaginator)
        """

if TYPE_CHECKING:
    _ListStandardsControlAssociationsPaginatorBase = Paginator[
        ListStandardsControlAssociationsResponseTypeDef
    ]
else:
    _ListStandardsControlAssociationsPaginatorBase = Paginator  # type: ignore[assignment]

class ListStandardsControlAssociationsPaginator(_ListStandardsControlAssociationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListStandardsControlAssociations.html#SecurityHub.Paginator.ListStandardsControlAssociations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#liststandardscontrolassociationspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListStandardsControlAssociationsRequestPaginateTypeDef]
    ) -> PageIterator[ListStandardsControlAssociationsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/paginator/ListStandardsControlAssociations.html#SecurityHub.Paginator.ListStandardsControlAssociations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_securityhub/paginators/#liststandardscontrolassociationspaginator)
        """
