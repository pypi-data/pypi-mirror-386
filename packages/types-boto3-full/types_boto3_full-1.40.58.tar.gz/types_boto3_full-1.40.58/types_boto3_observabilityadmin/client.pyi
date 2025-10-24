"""
Type annotations for observabilityadmin service Client.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from types_boto3_observabilityadmin.client import CloudWatchObservabilityAdminServiceClient

    session = Session()
    client: CloudWatchObservabilityAdminServiceClient = session.client("observabilityadmin")
    ```
"""

from __future__ import annotations

import sys
from typing import Any, overload

from botocore.client import BaseClient, ClientMeta
from botocore.errorfactory import BaseClientExceptions
from botocore.exceptions import ClientError as BotocoreClientError

from .paginator import (
    ListCentralizationRulesForOrganizationPaginator,
    ListResourceTelemetryForOrganizationPaginator,
    ListResourceTelemetryPaginator,
    ListTelemetryRulesForOrganizationPaginator,
    ListTelemetryRulesPaginator,
)
from .type_defs import (
    CreateCentralizationRuleForOrganizationInputTypeDef,
    CreateCentralizationRuleForOrganizationOutputTypeDef,
    CreateTelemetryRuleForOrganizationInputTypeDef,
    CreateTelemetryRuleForOrganizationOutputTypeDef,
    CreateTelemetryRuleInputTypeDef,
    CreateTelemetryRuleOutputTypeDef,
    DeleteCentralizationRuleForOrganizationInputTypeDef,
    DeleteTelemetryRuleForOrganizationInputTypeDef,
    DeleteTelemetryRuleInputTypeDef,
    EmptyResponseMetadataTypeDef,
    GetCentralizationRuleForOrganizationInputTypeDef,
    GetCentralizationRuleForOrganizationOutputTypeDef,
    GetTelemetryEnrichmentStatusOutputTypeDef,
    GetTelemetryEvaluationStatusForOrganizationOutputTypeDef,
    GetTelemetryEvaluationStatusOutputTypeDef,
    GetTelemetryRuleForOrganizationInputTypeDef,
    GetTelemetryRuleForOrganizationOutputTypeDef,
    GetTelemetryRuleInputTypeDef,
    GetTelemetryRuleOutputTypeDef,
    ListCentralizationRulesForOrganizationInputTypeDef,
    ListCentralizationRulesForOrganizationOutputTypeDef,
    ListResourceTelemetryForOrganizationInputTypeDef,
    ListResourceTelemetryForOrganizationOutputTypeDef,
    ListResourceTelemetryInputTypeDef,
    ListResourceTelemetryOutputTypeDef,
    ListTagsForResourceInputTypeDef,
    ListTagsForResourceOutputTypeDef,
    ListTelemetryRulesForOrganizationInputTypeDef,
    ListTelemetryRulesForOrganizationOutputTypeDef,
    ListTelemetryRulesInputTypeDef,
    ListTelemetryRulesOutputTypeDef,
    StartTelemetryEnrichmentOutputTypeDef,
    StopTelemetryEnrichmentOutputTypeDef,
    TagResourceInputTypeDef,
    UntagResourceInputTypeDef,
    UpdateCentralizationRuleForOrganizationInputTypeDef,
    UpdateCentralizationRuleForOrganizationOutputTypeDef,
    UpdateTelemetryRuleForOrganizationInputTypeDef,
    UpdateTelemetryRuleForOrganizationOutputTypeDef,
    UpdateTelemetryRuleInputTypeDef,
    UpdateTelemetryRuleOutputTypeDef,
)

if sys.version_info >= (3, 9):
    from builtins import type as Type
    from collections.abc import Mapping
else:
    from typing import Mapping, Type
if sys.version_info >= (3, 12):
    from typing import Literal, Unpack
else:
    from typing_extensions import Literal, Unpack

__all__ = ("CloudWatchObservabilityAdminServiceClient",)

class Exceptions(BaseClientExceptions):
    AccessDeniedException: Type[BotocoreClientError]
    ClientError: Type[BotocoreClientError]
    ConflictException: Type[BotocoreClientError]
    InternalServerException: Type[BotocoreClientError]
    ResourceNotFoundException: Type[BotocoreClientError]
    ServiceQuotaExceededException: Type[BotocoreClientError]
    TooManyRequestsException: Type[BotocoreClientError]
    ValidationException: Type[BotocoreClientError]

class CloudWatchObservabilityAdminServiceClient(BaseClient):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin.html#CloudWatchObservabilityAdminService.Client)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/)
    """

    meta: ClientMeta

    @property
    def exceptions(self) -> Exceptions:
        """
        CloudWatchObservabilityAdminServiceClient exceptions.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin.html#CloudWatchObservabilityAdminService.Client)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#exceptions)
        """

    def can_paginate(self, operation_name: str) -> bool:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/can_paginate.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#can_paginate)
        """

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Mapping[str, Any] = ...,
        ExpiresIn: int = 3600,
        HttpMethod: str = ...,
    ) -> str:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/generate_presigned_url.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#generate_presigned_url)
        """

    def create_centralization_rule_for_organization(
        self, **kwargs: Unpack[CreateCentralizationRuleForOrganizationInputTypeDef]
    ) -> CreateCentralizationRuleForOrganizationOutputTypeDef:
        """
        Creates a centralization rule that applies across an Amazon Web Services
        Organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/create_centralization_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#create_centralization_rule_for_organization)
        """

    def create_telemetry_rule(
        self, **kwargs: Unpack[CreateTelemetryRuleInputTypeDef]
    ) -> CreateTelemetryRuleOutputTypeDef:
        """
        Creates a telemetry rule that defines how telemetry should be configured for
        Amazon Web Services resources in your account.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/create_telemetry_rule.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#create_telemetry_rule)
        """

    def create_telemetry_rule_for_organization(
        self, **kwargs: Unpack[CreateTelemetryRuleForOrganizationInputTypeDef]
    ) -> CreateTelemetryRuleForOrganizationOutputTypeDef:
        """
        Creates a telemetry rule that applies across an Amazon Web Services
        Organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/create_telemetry_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#create_telemetry_rule_for_organization)
        """

    def delete_centralization_rule_for_organization(
        self, **kwargs: Unpack[DeleteCentralizationRuleForOrganizationInputTypeDef]
    ) -> EmptyResponseMetadataTypeDef:
        """
        Deletes an organization-wide centralization rule.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/delete_centralization_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#delete_centralization_rule_for_organization)
        """

    def delete_telemetry_rule(
        self, **kwargs: Unpack[DeleteTelemetryRuleInputTypeDef]
    ) -> EmptyResponseMetadataTypeDef:
        """
        Deletes a telemetry rule from your account.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/delete_telemetry_rule.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#delete_telemetry_rule)
        """

    def delete_telemetry_rule_for_organization(
        self, **kwargs: Unpack[DeleteTelemetryRuleForOrganizationInputTypeDef]
    ) -> EmptyResponseMetadataTypeDef:
        """
        Deletes an organization-wide telemetry rule.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/delete_telemetry_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#delete_telemetry_rule_for_organization)
        """

    def get_centralization_rule_for_organization(
        self, **kwargs: Unpack[GetCentralizationRuleForOrganizationInputTypeDef]
    ) -> GetCentralizationRuleForOrganizationOutputTypeDef:
        """
        Retrieves the details of a specific organization centralization rule.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_centralization_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_centralization_rule_for_organization)
        """

    def get_telemetry_enrichment_status(self) -> GetTelemetryEnrichmentStatusOutputTypeDef:
        """
        Returns the current status of the resource tags for telemetry feature, which
        enhances telemetry data with additional resource metadata from Amazon Web
        Services Resource Explorer.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_telemetry_enrichment_status.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_telemetry_enrichment_status)
        """

    def get_telemetry_evaluation_status(self) -> GetTelemetryEvaluationStatusOutputTypeDef:
        """
        Returns the current onboarding status of the telemetry config feature,
        including the status of the feature and reason the feature failed to start or
        stop.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_telemetry_evaluation_status.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_telemetry_evaluation_status)
        """

    def get_telemetry_evaluation_status_for_organization(
        self,
    ) -> GetTelemetryEvaluationStatusForOrganizationOutputTypeDef:
        """
        This returns the onboarding status of the telemetry configuration feature for
        the organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_telemetry_evaluation_status_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_telemetry_evaluation_status_for_organization)
        """

    def get_telemetry_rule(
        self, **kwargs: Unpack[GetTelemetryRuleInputTypeDef]
    ) -> GetTelemetryRuleOutputTypeDef:
        """
        Retrieves the details of a specific telemetry rule in your account.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_telemetry_rule.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_telemetry_rule)
        """

    def get_telemetry_rule_for_organization(
        self, **kwargs: Unpack[GetTelemetryRuleForOrganizationInputTypeDef]
    ) -> GetTelemetryRuleForOrganizationOutputTypeDef:
        """
        Retrieves the details of a specific organization telemetry rule.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_telemetry_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_telemetry_rule_for_organization)
        """

    def list_centralization_rules_for_organization(
        self, **kwargs: Unpack[ListCentralizationRulesForOrganizationInputTypeDef]
    ) -> ListCentralizationRulesForOrganizationOutputTypeDef:
        """
        Lists all centralization rules in your organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_centralization_rules_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_centralization_rules_for_organization)
        """

    def list_resource_telemetry(
        self, **kwargs: Unpack[ListResourceTelemetryInputTypeDef]
    ) -> ListResourceTelemetryOutputTypeDef:
        """
        Returns a list of telemetry configurations for Amazon Web Services resources
        supported by telemetry config.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_resource_telemetry.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_resource_telemetry)
        """

    def list_resource_telemetry_for_organization(
        self, **kwargs: Unpack[ListResourceTelemetryForOrganizationInputTypeDef]
    ) -> ListResourceTelemetryForOrganizationOutputTypeDef:
        """
        Returns a list of telemetry configurations for Amazon Web Services resources
        supported by telemetry config in the organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_resource_telemetry_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_resource_telemetry_for_organization)
        """

    def list_tags_for_resource(
        self, **kwargs: Unpack[ListTagsForResourceInputTypeDef]
    ) -> ListTagsForResourceOutputTypeDef:
        """
        Lists all tags attached to the specified telemetry rule resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_tags_for_resource.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_tags_for_resource)
        """

    def list_telemetry_rules(
        self, **kwargs: Unpack[ListTelemetryRulesInputTypeDef]
    ) -> ListTelemetryRulesOutputTypeDef:
        """
        Lists all telemetry rules in your account.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_telemetry_rules.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_telemetry_rules)
        """

    def list_telemetry_rules_for_organization(
        self, **kwargs: Unpack[ListTelemetryRulesForOrganizationInputTypeDef]
    ) -> ListTelemetryRulesForOrganizationOutputTypeDef:
        """
        Lists all telemetry rules in your organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/list_telemetry_rules_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#list_telemetry_rules_for_organization)
        """

    def start_telemetry_enrichment(self) -> StartTelemetryEnrichmentOutputTypeDef:
        """
        Enables the resource tags for telemetry feature for your account, which
        enhances telemetry data with additional resource metadata from Amazon Web
        Services Resource Explorer to provide richer context for monitoring and
        observability.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/start_telemetry_enrichment.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#start_telemetry_enrichment)
        """

    def start_telemetry_evaluation(self) -> EmptyResponseMetadataTypeDef:
        """
        This action begins onboarding the caller Amazon Web Services account to the
        telemetry config feature.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/start_telemetry_evaluation.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#start_telemetry_evaluation)
        """

    def start_telemetry_evaluation_for_organization(self) -> EmptyResponseMetadataTypeDef:
        """
        This actions begins onboarding the organization and all member accounts to the
        telemetry config feature.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/start_telemetry_evaluation_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#start_telemetry_evaluation_for_organization)
        """

    def stop_telemetry_enrichment(self) -> StopTelemetryEnrichmentOutputTypeDef:
        """
        Disables the resource tags for telemetry feature for your account, stopping the
        enhancement of telemetry data with additional resource metadata.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/stop_telemetry_enrichment.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#stop_telemetry_enrichment)
        """

    def stop_telemetry_evaluation(self) -> EmptyResponseMetadataTypeDef:
        """
        This action begins offboarding the caller Amazon Web Services account from the
        telemetry config feature.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/stop_telemetry_evaluation.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#stop_telemetry_evaluation)
        """

    def stop_telemetry_evaluation_for_organization(self) -> EmptyResponseMetadataTypeDef:
        """
        This action offboards the Organization of the caller Amazon Web Services
        account from the telemetry config feature.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/stop_telemetry_evaluation_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#stop_telemetry_evaluation_for_organization)
        """

    def tag_resource(
        self, **kwargs: Unpack[TagResourceInputTypeDef]
    ) -> EmptyResponseMetadataTypeDef:
        """
        Adds or updates tags for a telemetry rule resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/tag_resource.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#tag_resource)
        """

    def untag_resource(
        self, **kwargs: Unpack[UntagResourceInputTypeDef]
    ) -> EmptyResponseMetadataTypeDef:
        """
        Removes tags from a telemetry rule resource.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/untag_resource.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#untag_resource)
        """

    def update_centralization_rule_for_organization(
        self, **kwargs: Unpack[UpdateCentralizationRuleForOrganizationInputTypeDef]
    ) -> UpdateCentralizationRuleForOrganizationOutputTypeDef:
        """
        Updates an existing centralization rule that applies across an Amazon Web
        Services Organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/update_centralization_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#update_centralization_rule_for_organization)
        """

    def update_telemetry_rule(
        self, **kwargs: Unpack[UpdateTelemetryRuleInputTypeDef]
    ) -> UpdateTelemetryRuleOutputTypeDef:
        """
        Updates an existing telemetry rule in your account.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/update_telemetry_rule.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#update_telemetry_rule)
        """

    def update_telemetry_rule_for_organization(
        self, **kwargs: Unpack[UpdateTelemetryRuleForOrganizationInputTypeDef]
    ) -> UpdateTelemetryRuleForOrganizationOutputTypeDef:
        """
        Updates an existing telemetry rule that applies across an Amazon Web Services
        Organization.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/update_telemetry_rule_for_organization.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#update_telemetry_rule_for_organization)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_centralization_rules_for_organization"]
    ) -> ListCentralizationRulesForOrganizationPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_paginator.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_resource_telemetry_for_organization"]
    ) -> ListResourceTelemetryForOrganizationPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_paginator.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_resource_telemetry"]
    ) -> ListResourceTelemetryPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_paginator.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_telemetry_rules_for_organization"]
    ) -> ListTelemetryRulesForOrganizationPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_paginator.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_telemetry_rules"]
    ) -> ListTelemetryRulesPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/observabilityadmin/client/get_paginator.html)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_observabilityadmin/client/#get_paginator)
        """
