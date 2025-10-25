"""
Main interface for quicksight service.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_quicksight/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_quicksight import (
        Client,
        DescribeFolderPermissionsPaginator,
        DescribeFolderResolvedPermissionsPaginator,
        ListActionConnectorsPaginator,
        ListAnalysesPaginator,
        ListAssetBundleExportJobsPaginator,
        ListAssetBundleImportJobsPaginator,
        ListBrandsPaginator,
        ListCustomPermissionsPaginator,
        ListDashboardVersionsPaginator,
        ListDashboardsPaginator,
        ListDataSetsPaginator,
        ListDataSourcesPaginator,
        ListFlowsPaginator,
        ListFolderMembersPaginator,
        ListFoldersForResourcePaginator,
        ListFoldersPaginator,
        ListGroupMembershipsPaginator,
        ListGroupsPaginator,
        ListIAMPolicyAssignmentsForUserPaginator,
        ListIAMPolicyAssignmentsPaginator,
        ListIngestionsPaginator,
        ListNamespacesPaginator,
        ListRoleMembershipsPaginator,
        ListTemplateAliasesPaginator,
        ListTemplateVersionsPaginator,
        ListTemplatesPaginator,
        ListThemeVersionsPaginator,
        ListThemesPaginator,
        ListUserGroupsPaginator,
        ListUsersPaginator,
        QuickSightClient,
        SearchActionConnectorsPaginator,
        SearchAnalysesPaginator,
        SearchDashboardsPaginator,
        SearchDataSetsPaginator,
        SearchDataSourcesPaginator,
        SearchFlowsPaginator,
        SearchFoldersPaginator,
        SearchGroupsPaginator,
        SearchTopicsPaginator,
    )

    session = Session()
    client: QuickSightClient = session.client("quicksight")

    describe_folder_permissions_paginator: DescribeFolderPermissionsPaginator = client.get_paginator("describe_folder_permissions")
    describe_folder_resolved_permissions_paginator: DescribeFolderResolvedPermissionsPaginator = client.get_paginator("describe_folder_resolved_permissions")
    list_action_connectors_paginator: ListActionConnectorsPaginator = client.get_paginator("list_action_connectors")
    list_analyses_paginator: ListAnalysesPaginator = client.get_paginator("list_analyses")
    list_asset_bundle_export_jobs_paginator: ListAssetBundleExportJobsPaginator = client.get_paginator("list_asset_bundle_export_jobs")
    list_asset_bundle_import_jobs_paginator: ListAssetBundleImportJobsPaginator = client.get_paginator("list_asset_bundle_import_jobs")
    list_brands_paginator: ListBrandsPaginator = client.get_paginator("list_brands")
    list_custom_permissions_paginator: ListCustomPermissionsPaginator = client.get_paginator("list_custom_permissions")
    list_dashboard_versions_paginator: ListDashboardVersionsPaginator = client.get_paginator("list_dashboard_versions")
    list_dashboards_paginator: ListDashboardsPaginator = client.get_paginator("list_dashboards")
    list_data_sets_paginator: ListDataSetsPaginator = client.get_paginator("list_data_sets")
    list_data_sources_paginator: ListDataSourcesPaginator = client.get_paginator("list_data_sources")
    list_flows_paginator: ListFlowsPaginator = client.get_paginator("list_flows")
    list_folder_members_paginator: ListFolderMembersPaginator = client.get_paginator("list_folder_members")
    list_folders_for_resource_paginator: ListFoldersForResourcePaginator = client.get_paginator("list_folders_for_resource")
    list_folders_paginator: ListFoldersPaginator = client.get_paginator("list_folders")
    list_group_memberships_paginator: ListGroupMembershipsPaginator = client.get_paginator("list_group_memberships")
    list_groups_paginator: ListGroupsPaginator = client.get_paginator("list_groups")
    list_iam_policy_assignments_for_user_paginator: ListIAMPolicyAssignmentsForUserPaginator = client.get_paginator("list_iam_policy_assignments_for_user")
    list_iam_policy_assignments_paginator: ListIAMPolicyAssignmentsPaginator = client.get_paginator("list_iam_policy_assignments")
    list_ingestions_paginator: ListIngestionsPaginator = client.get_paginator("list_ingestions")
    list_namespaces_paginator: ListNamespacesPaginator = client.get_paginator("list_namespaces")
    list_role_memberships_paginator: ListRoleMembershipsPaginator = client.get_paginator("list_role_memberships")
    list_template_aliases_paginator: ListTemplateAliasesPaginator = client.get_paginator("list_template_aliases")
    list_template_versions_paginator: ListTemplateVersionsPaginator = client.get_paginator("list_template_versions")
    list_templates_paginator: ListTemplatesPaginator = client.get_paginator("list_templates")
    list_theme_versions_paginator: ListThemeVersionsPaginator = client.get_paginator("list_theme_versions")
    list_themes_paginator: ListThemesPaginator = client.get_paginator("list_themes")
    list_user_groups_paginator: ListUserGroupsPaginator = client.get_paginator("list_user_groups")
    list_users_paginator: ListUsersPaginator = client.get_paginator("list_users")
    search_action_connectors_paginator: SearchActionConnectorsPaginator = client.get_paginator("search_action_connectors")
    search_analyses_paginator: SearchAnalysesPaginator = client.get_paginator("search_analyses")
    search_dashboards_paginator: SearchDashboardsPaginator = client.get_paginator("search_dashboards")
    search_data_sets_paginator: SearchDataSetsPaginator = client.get_paginator("search_data_sets")
    search_data_sources_paginator: SearchDataSourcesPaginator = client.get_paginator("search_data_sources")
    search_flows_paginator: SearchFlowsPaginator = client.get_paginator("search_flows")
    search_folders_paginator: SearchFoldersPaginator = client.get_paginator("search_folders")
    search_groups_paginator: SearchGroupsPaginator = client.get_paginator("search_groups")
    search_topics_paginator: SearchTopicsPaginator = client.get_paginator("search_topics")
    ```
"""

from .client import QuickSightClient
from .paginator import (
    DescribeFolderPermissionsPaginator,
    DescribeFolderResolvedPermissionsPaginator,
    ListActionConnectorsPaginator,
    ListAnalysesPaginator,
    ListAssetBundleExportJobsPaginator,
    ListAssetBundleImportJobsPaginator,
    ListBrandsPaginator,
    ListCustomPermissionsPaginator,
    ListDashboardsPaginator,
    ListDashboardVersionsPaginator,
    ListDataSetsPaginator,
    ListDataSourcesPaginator,
    ListFlowsPaginator,
    ListFolderMembersPaginator,
    ListFoldersForResourcePaginator,
    ListFoldersPaginator,
    ListGroupMembershipsPaginator,
    ListGroupsPaginator,
    ListIAMPolicyAssignmentsForUserPaginator,
    ListIAMPolicyAssignmentsPaginator,
    ListIngestionsPaginator,
    ListNamespacesPaginator,
    ListRoleMembershipsPaginator,
    ListTemplateAliasesPaginator,
    ListTemplatesPaginator,
    ListTemplateVersionsPaginator,
    ListThemesPaginator,
    ListThemeVersionsPaginator,
    ListUserGroupsPaginator,
    ListUsersPaginator,
    SearchActionConnectorsPaginator,
    SearchAnalysesPaginator,
    SearchDashboardsPaginator,
    SearchDataSetsPaginator,
    SearchDataSourcesPaginator,
    SearchFlowsPaginator,
    SearchFoldersPaginator,
    SearchGroupsPaginator,
    SearchTopicsPaginator,
)

Client = QuickSightClient

__all__ = (
    "Client",
    "DescribeFolderPermissionsPaginator",
    "DescribeFolderResolvedPermissionsPaginator",
    "ListActionConnectorsPaginator",
    "ListAnalysesPaginator",
    "ListAssetBundleExportJobsPaginator",
    "ListAssetBundleImportJobsPaginator",
    "ListBrandsPaginator",
    "ListCustomPermissionsPaginator",
    "ListDashboardVersionsPaginator",
    "ListDashboardsPaginator",
    "ListDataSetsPaginator",
    "ListDataSourcesPaginator",
    "ListFlowsPaginator",
    "ListFolderMembersPaginator",
    "ListFoldersForResourcePaginator",
    "ListFoldersPaginator",
    "ListGroupMembershipsPaginator",
    "ListGroupsPaginator",
    "ListIAMPolicyAssignmentsForUserPaginator",
    "ListIAMPolicyAssignmentsPaginator",
    "ListIngestionsPaginator",
    "ListNamespacesPaginator",
    "ListRoleMembershipsPaginator",
    "ListTemplateAliasesPaginator",
    "ListTemplateVersionsPaginator",
    "ListTemplatesPaginator",
    "ListThemeVersionsPaginator",
    "ListThemesPaginator",
    "ListUserGroupsPaginator",
    "ListUsersPaginator",
    "QuickSightClient",
    "SearchActionConnectorsPaginator",
    "SearchAnalysesPaginator",
    "SearchDashboardsPaginator",
    "SearchDataSetsPaginator",
    "SearchDataSourcesPaginator",
    "SearchFlowsPaginator",
    "SearchFoldersPaginator",
    "SearchGroupsPaginator",
    "SearchTopicsPaginator",
)
