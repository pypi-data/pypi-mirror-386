"""
Type annotations for osis service type definitions.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_osis/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from types_boto3_osis.type_defs import BufferOptionsTypeDef

    data: BufferOptionsTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Union

from .literals import (
    ChangeProgressStageStatusesType,
    ChangeProgressStatusesType,
    PipelineEndpointStatusType,
    PipelineStatusType,
    VpcEndpointManagementType,
)

if sys.version_info >= (3, 9):
    from builtins import dict as Dict
    from builtins import list as List
    from collections.abc import Sequence
else:
    from typing import Dict, List, Sequence
if sys.version_info >= (3, 12):
    from typing import Literal, NotRequired, TypedDict
else:
    from typing_extensions import Literal, NotRequired, TypedDict


__all__ = (
    "BufferOptionsTypeDef",
    "ChangeProgressStageTypeDef",
    "ChangeProgressStatusTypeDef",
    "CloudWatchLogDestinationTypeDef",
    "CreatePipelineEndpointRequestTypeDef",
    "CreatePipelineEndpointResponseTypeDef",
    "CreatePipelineRequestTypeDef",
    "CreatePipelineResponseTypeDef",
    "DeletePipelineEndpointRequestTypeDef",
    "DeletePipelineRequestTypeDef",
    "DeleteResourcePolicyRequestTypeDef",
    "EncryptionAtRestOptionsTypeDef",
    "GetPipelineBlueprintRequestTypeDef",
    "GetPipelineBlueprintResponseTypeDef",
    "GetPipelineChangeProgressRequestTypeDef",
    "GetPipelineChangeProgressResponseTypeDef",
    "GetPipelineRequestTypeDef",
    "GetPipelineResponseTypeDef",
    "GetResourcePolicyRequestTypeDef",
    "GetResourcePolicyResponseTypeDef",
    "ListPipelineBlueprintsResponseTypeDef",
    "ListPipelineEndpointConnectionsRequestPaginateTypeDef",
    "ListPipelineEndpointConnectionsRequestTypeDef",
    "ListPipelineEndpointConnectionsResponseTypeDef",
    "ListPipelineEndpointsRequestPaginateTypeDef",
    "ListPipelineEndpointsRequestTypeDef",
    "ListPipelineEndpointsResponseTypeDef",
    "ListPipelinesRequestTypeDef",
    "ListPipelinesResponseTypeDef",
    "ListTagsForResourceRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "LogPublishingOptionsTypeDef",
    "PaginatorConfigTypeDef",
    "PipelineBlueprintSummaryTypeDef",
    "PipelineBlueprintTypeDef",
    "PipelineDestinationTypeDef",
    "PipelineEndpointConnectionTypeDef",
    "PipelineEndpointTypeDef",
    "PipelineEndpointVpcOptionsOutputTypeDef",
    "PipelineEndpointVpcOptionsTypeDef",
    "PipelineEndpointVpcOptionsUnionTypeDef",
    "PipelineStatusReasonTypeDef",
    "PipelineSummaryTypeDef",
    "PipelineTypeDef",
    "PutResourcePolicyRequestTypeDef",
    "PutResourcePolicyResponseTypeDef",
    "ResponseMetadataTypeDef",
    "RevokePipelineEndpointConnectionsRequestTypeDef",
    "RevokePipelineEndpointConnectionsResponseTypeDef",
    "ServiceVpcEndpointTypeDef",
    "StartPipelineRequestTypeDef",
    "StartPipelineResponseTypeDef",
    "StopPipelineRequestTypeDef",
    "StopPipelineResponseTypeDef",
    "TagResourceRequestTypeDef",
    "TagTypeDef",
    "UntagResourceRequestTypeDef",
    "UpdatePipelineRequestTypeDef",
    "UpdatePipelineResponseTypeDef",
    "ValidatePipelineRequestTypeDef",
    "ValidatePipelineResponseTypeDef",
    "ValidationMessageTypeDef",
    "VpcAttachmentOptionsTypeDef",
    "VpcEndpointTypeDef",
    "VpcOptionsOutputTypeDef",
    "VpcOptionsTypeDef",
    "VpcOptionsUnionTypeDef",
)


class BufferOptionsTypeDef(TypedDict):
    PersistentBufferEnabled: bool


class ChangeProgressStageTypeDef(TypedDict):
    Name: NotRequired[str]
    Status: NotRequired[ChangeProgressStageStatusesType]
    Description: NotRequired[str]
    LastUpdatedAt: NotRequired[datetime]


class CloudWatchLogDestinationTypeDef(TypedDict):
    LogGroup: str


class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]


class EncryptionAtRestOptionsTypeDef(TypedDict):
    KmsKeyArn: str


class TagTypeDef(TypedDict):
    Key: str
    Value: str


class DeletePipelineEndpointRequestTypeDef(TypedDict):
    EndpointId: str


class DeletePipelineRequestTypeDef(TypedDict):
    PipelineName: str


class DeleteResourcePolicyRequestTypeDef(TypedDict):
    ResourceArn: str


class GetPipelineBlueprintRequestTypeDef(TypedDict):
    BlueprintName: str
    Format: NotRequired[str]


class PipelineBlueprintTypeDef(TypedDict):
    BlueprintName: NotRequired[str]
    PipelineConfigurationBody: NotRequired[str]
    DisplayName: NotRequired[str]
    DisplayDescription: NotRequired[str]
    Service: NotRequired[str]
    UseCase: NotRequired[str]


class GetPipelineChangeProgressRequestTypeDef(TypedDict):
    PipelineName: str


class GetPipelineRequestTypeDef(TypedDict):
    PipelineName: str


class GetResourcePolicyRequestTypeDef(TypedDict):
    ResourceArn: str


class PipelineBlueprintSummaryTypeDef(TypedDict):
    BlueprintName: NotRequired[str]
    DisplayName: NotRequired[str]
    DisplayDescription: NotRequired[str]
    Service: NotRequired[str]
    UseCase: NotRequired[str]


class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]


class ListPipelineEndpointConnectionsRequestTypeDef(TypedDict):
    MaxResults: NotRequired[int]
    NextToken: NotRequired[str]


class PipelineEndpointConnectionTypeDef(TypedDict):
    PipelineArn: NotRequired[str]
    EndpointId: NotRequired[str]
    Status: NotRequired[PipelineEndpointStatusType]
    VpcEndpointOwner: NotRequired[str]


class ListPipelineEndpointsRequestTypeDef(TypedDict):
    MaxResults: NotRequired[int]
    NextToken: NotRequired[str]


class ListPipelinesRequestTypeDef(TypedDict):
    MaxResults: NotRequired[int]
    NextToken: NotRequired[str]


class ListTagsForResourceRequestTypeDef(TypedDict):
    Arn: str


PipelineDestinationTypeDef = TypedDict(
    "PipelineDestinationTypeDef",
    {
        "ServiceName": NotRequired[str],
        "Endpoint": NotRequired[str],
    },
)


class PipelineEndpointVpcOptionsOutputTypeDef(TypedDict):
    SubnetIds: NotRequired[List[str]]
    SecurityGroupIds: NotRequired[List[str]]


class PipelineEndpointVpcOptionsTypeDef(TypedDict):
    SubnetIds: NotRequired[Sequence[str]]
    SecurityGroupIds: NotRequired[Sequence[str]]


class PipelineStatusReasonTypeDef(TypedDict):
    Description: NotRequired[str]


ServiceVpcEndpointTypeDef = TypedDict(
    "ServiceVpcEndpointTypeDef",
    {
        "ServiceName": NotRequired[Literal["OPENSEARCH_SERVERLESS"]],
        "VpcEndpointId": NotRequired[str],
    },
)


class PutResourcePolicyRequestTypeDef(TypedDict):
    ResourceArn: str
    Policy: str


class RevokePipelineEndpointConnectionsRequestTypeDef(TypedDict):
    PipelineArn: str
    EndpointIds: Sequence[str]


class StartPipelineRequestTypeDef(TypedDict):
    PipelineName: str


class StopPipelineRequestTypeDef(TypedDict):
    PipelineName: str


class UntagResourceRequestTypeDef(TypedDict):
    Arn: str
    TagKeys: Sequence[str]


class ValidatePipelineRequestTypeDef(TypedDict):
    PipelineConfigurationBody: str


class ValidationMessageTypeDef(TypedDict):
    Message: NotRequired[str]


class VpcAttachmentOptionsTypeDef(TypedDict):
    AttachToVpc: bool
    CidrBlock: NotRequired[str]


class ChangeProgressStatusTypeDef(TypedDict):
    StartTime: NotRequired[datetime]
    Status: NotRequired[ChangeProgressStatusesType]
    TotalNumberOfStages: NotRequired[int]
    ChangeProgressStages: NotRequired[List[ChangeProgressStageTypeDef]]


class LogPublishingOptionsTypeDef(TypedDict):
    IsLoggingEnabled: NotRequired[bool]
    CloudWatchLogDestination: NotRequired[CloudWatchLogDestinationTypeDef]


class CreatePipelineEndpointResponseTypeDef(TypedDict):
    PipelineArn: str
    EndpointId: str
    Status: PipelineEndpointStatusType
    VpcId: str
    ResponseMetadata: ResponseMetadataTypeDef


class GetResourcePolicyResponseTypeDef(TypedDict):
    ResourceArn: str
    Policy: str
    ResponseMetadata: ResponseMetadataTypeDef


class PutResourcePolicyResponseTypeDef(TypedDict):
    ResourceArn: str
    Policy: str
    ResponseMetadata: ResponseMetadataTypeDef


class RevokePipelineEndpointConnectionsResponseTypeDef(TypedDict):
    PipelineArn: str
    ResponseMetadata: ResponseMetadataTypeDef


class ListTagsForResourceResponseTypeDef(TypedDict):
    Tags: List[TagTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef


class TagResourceRequestTypeDef(TypedDict):
    Arn: str
    Tags: Sequence[TagTypeDef]


class GetPipelineBlueprintResponseTypeDef(TypedDict):
    Blueprint: PipelineBlueprintTypeDef
    Format: str
    ResponseMetadata: ResponseMetadataTypeDef


class ListPipelineBlueprintsResponseTypeDef(TypedDict):
    Blueprints: List[PipelineBlueprintSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef


class ListPipelineEndpointConnectionsRequestPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListPipelineEndpointsRequestPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]


class ListPipelineEndpointConnectionsResponseTypeDef(TypedDict):
    PipelineEndpointConnections: List[PipelineEndpointConnectionTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    NextToken: NotRequired[str]


class PipelineEndpointTypeDef(TypedDict):
    PipelineArn: NotRequired[str]
    EndpointId: NotRequired[str]
    Status: NotRequired[PipelineEndpointStatusType]
    VpcId: NotRequired[str]
    VpcOptions: NotRequired[PipelineEndpointVpcOptionsOutputTypeDef]
    IngestEndpointUrl: NotRequired[str]


PipelineEndpointVpcOptionsUnionTypeDef = Union[
    PipelineEndpointVpcOptionsTypeDef, PipelineEndpointVpcOptionsOutputTypeDef
]


class PipelineSummaryTypeDef(TypedDict):
    Status: NotRequired[PipelineStatusType]
    StatusReason: NotRequired[PipelineStatusReasonTypeDef]
    PipelineName: NotRequired[str]
    PipelineArn: NotRequired[str]
    MinUnits: NotRequired[int]
    MaxUnits: NotRequired[int]
    CreatedAt: NotRequired[datetime]
    LastUpdatedAt: NotRequired[datetime]
    Destinations: NotRequired[List[PipelineDestinationTypeDef]]
    Tags: NotRequired[List[TagTypeDef]]


class ValidatePipelineResponseTypeDef(TypedDict):
    isValid: bool
    Errors: List[ValidationMessageTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef


class VpcOptionsOutputTypeDef(TypedDict):
    SubnetIds: List[str]
    SecurityGroupIds: NotRequired[List[str]]
    VpcAttachmentOptions: NotRequired[VpcAttachmentOptionsTypeDef]
    VpcEndpointManagement: NotRequired[VpcEndpointManagementType]


class VpcOptionsTypeDef(TypedDict):
    SubnetIds: Sequence[str]
    SecurityGroupIds: NotRequired[Sequence[str]]
    VpcAttachmentOptions: NotRequired[VpcAttachmentOptionsTypeDef]
    VpcEndpointManagement: NotRequired[VpcEndpointManagementType]


class GetPipelineChangeProgressResponseTypeDef(TypedDict):
    ChangeProgressStatuses: List[ChangeProgressStatusTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef


class UpdatePipelineRequestTypeDef(TypedDict):
    PipelineName: str
    MinUnits: NotRequired[int]
    MaxUnits: NotRequired[int]
    PipelineConfigurationBody: NotRequired[str]
    LogPublishingOptions: NotRequired[LogPublishingOptionsTypeDef]
    BufferOptions: NotRequired[BufferOptionsTypeDef]
    EncryptionAtRestOptions: NotRequired[EncryptionAtRestOptionsTypeDef]
    PipelineRoleArn: NotRequired[str]


class ListPipelineEndpointsResponseTypeDef(TypedDict):
    PipelineEndpoints: List[PipelineEndpointTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    NextToken: NotRequired[str]


class CreatePipelineEndpointRequestTypeDef(TypedDict):
    PipelineArn: str
    VpcOptions: PipelineEndpointVpcOptionsUnionTypeDef


class ListPipelinesResponseTypeDef(TypedDict):
    Pipelines: List[PipelineSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    NextToken: NotRequired[str]


class VpcEndpointTypeDef(TypedDict):
    VpcEndpointId: NotRequired[str]
    VpcId: NotRequired[str]
    VpcOptions: NotRequired[VpcOptionsOutputTypeDef]


VpcOptionsUnionTypeDef = Union[VpcOptionsTypeDef, VpcOptionsOutputTypeDef]


class PipelineTypeDef(TypedDict):
    PipelineName: NotRequired[str]
    PipelineArn: NotRequired[str]
    MinUnits: NotRequired[int]
    MaxUnits: NotRequired[int]
    Status: NotRequired[PipelineStatusType]
    StatusReason: NotRequired[PipelineStatusReasonTypeDef]
    PipelineConfigurationBody: NotRequired[str]
    CreatedAt: NotRequired[datetime]
    LastUpdatedAt: NotRequired[datetime]
    IngestEndpointUrls: NotRequired[List[str]]
    LogPublishingOptions: NotRequired[LogPublishingOptionsTypeDef]
    VpcEndpoints: NotRequired[List[VpcEndpointTypeDef]]
    BufferOptions: NotRequired[BufferOptionsTypeDef]
    EncryptionAtRestOptions: NotRequired[EncryptionAtRestOptionsTypeDef]
    VpcEndpointService: NotRequired[str]
    ServiceVpcEndpoints: NotRequired[List[ServiceVpcEndpointTypeDef]]
    Destinations: NotRequired[List[PipelineDestinationTypeDef]]
    Tags: NotRequired[List[TagTypeDef]]
    PipelineRoleArn: NotRequired[str]


class CreatePipelineRequestTypeDef(TypedDict):
    PipelineName: str
    MinUnits: int
    MaxUnits: int
    PipelineConfigurationBody: str
    LogPublishingOptions: NotRequired[LogPublishingOptionsTypeDef]
    VpcOptions: NotRequired[VpcOptionsUnionTypeDef]
    BufferOptions: NotRequired[BufferOptionsTypeDef]
    EncryptionAtRestOptions: NotRequired[EncryptionAtRestOptionsTypeDef]
    Tags: NotRequired[Sequence[TagTypeDef]]
    PipelineRoleArn: NotRequired[str]


class CreatePipelineResponseTypeDef(TypedDict):
    Pipeline: PipelineTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class GetPipelineResponseTypeDef(TypedDict):
    Pipeline: PipelineTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class StartPipelineResponseTypeDef(TypedDict):
    Pipeline: PipelineTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class StopPipelineResponseTypeDef(TypedDict):
    Pipeline: PipelineTypeDef
    ResponseMetadata: ResponseMetadataTypeDef


class UpdatePipelineResponseTypeDef(TypedDict):
    Pipeline: PipelineTypeDef
    ResponseMetadata: ResponseMetadataTypeDef
