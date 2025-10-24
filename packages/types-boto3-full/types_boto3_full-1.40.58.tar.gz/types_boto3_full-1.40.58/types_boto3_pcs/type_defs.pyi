"""
Type annotations for pcs service type definitions.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_pcs/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from types_boto3_pcs.type_defs import AccountingRequestTypeDef

    data: AccountingRequestTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from datetime import datetime

from .literals import (
    AccountingModeType,
    ClusterStatusType,
    ComputeNodeGroupStatusType,
    EndpointTypeType,
    NetworkTypeType,
    PurchaseOptionType,
    QueueStatusType,
    SizeType,
    SpotAllocationStrategyType,
)

if sys.version_info >= (3, 9):
    from builtins import dict as Dict
    from builtins import list as List
    from collections.abc import Mapping, Sequence
else:
    from typing import Dict, List, Mapping, Sequence
if sys.version_info >= (3, 12):
    from typing import Literal, NotRequired, TypedDict
else:
    from typing_extensions import Literal, NotRequired, TypedDict

__all__ = (
    "AccountingRequestTypeDef",
    "AccountingTypeDef",
    "ClusterSlurmConfigurationRequestTypeDef",
    "ClusterSlurmConfigurationTypeDef",
    "ClusterSummaryTypeDef",
    "ClusterTypeDef",
    "ComputeNodeGroupConfigurationTypeDef",
    "ComputeNodeGroupSlurmConfigurationRequestTypeDef",
    "ComputeNodeGroupSlurmConfigurationTypeDef",
    "ComputeNodeGroupSummaryTypeDef",
    "ComputeNodeGroupTypeDef",
    "CreateClusterRequestTypeDef",
    "CreateClusterResponseTypeDef",
    "CreateComputeNodeGroupRequestTypeDef",
    "CreateComputeNodeGroupResponseTypeDef",
    "CreateQueueRequestTypeDef",
    "CreateQueueResponseTypeDef",
    "CustomLaunchTemplateTypeDef",
    "DeleteClusterRequestTypeDef",
    "DeleteComputeNodeGroupRequestTypeDef",
    "DeleteQueueRequestTypeDef",
    "EmptyResponseMetadataTypeDef",
    "EndpointTypeDef",
    "ErrorInfoTypeDef",
    "GetClusterRequestTypeDef",
    "GetClusterResponseTypeDef",
    "GetComputeNodeGroupRequestTypeDef",
    "GetComputeNodeGroupResponseTypeDef",
    "GetQueueRequestTypeDef",
    "GetQueueResponseTypeDef",
    "InstanceConfigTypeDef",
    "ListClustersRequestPaginateTypeDef",
    "ListClustersRequestTypeDef",
    "ListClustersResponseTypeDef",
    "ListComputeNodeGroupsRequestPaginateTypeDef",
    "ListComputeNodeGroupsRequestTypeDef",
    "ListComputeNodeGroupsResponseTypeDef",
    "ListQueuesRequestPaginateTypeDef",
    "ListQueuesRequestTypeDef",
    "ListQueuesResponseTypeDef",
    "ListTagsForResourceRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "NetworkingRequestTypeDef",
    "NetworkingTypeDef",
    "PaginatorConfigTypeDef",
    "QueueSlurmConfigurationRequestTypeDef",
    "QueueSlurmConfigurationTypeDef",
    "QueueSummaryTypeDef",
    "QueueTypeDef",
    "RegisterComputeNodeGroupInstanceRequestTypeDef",
    "RegisterComputeNodeGroupInstanceResponseTypeDef",
    "ResponseMetadataTypeDef",
    "ScalingConfigurationRequestTypeDef",
    "ScalingConfigurationTypeDef",
    "SchedulerRequestTypeDef",
    "SchedulerTypeDef",
    "SlurmAuthKeyTypeDef",
    "SlurmCustomSettingTypeDef",
    "SpotOptionsTypeDef",
    "TagResourceRequestTypeDef",
    "UntagResourceRequestTypeDef",
    "UpdateAccountingRequestTypeDef",
    "UpdateClusterRequestTypeDef",
    "UpdateClusterResponseTypeDef",
    "UpdateClusterSlurmConfigurationRequestTypeDef",
    "UpdateComputeNodeGroupRequestTypeDef",
    "UpdateComputeNodeGroupResponseTypeDef",
    "UpdateComputeNodeGroupSlurmConfigurationRequestTypeDef",
    "UpdateQueueRequestTypeDef",
    "UpdateQueueResponseTypeDef",
    "UpdateQueueSlurmConfigurationRequestTypeDef",
)

class AccountingRequestTypeDef(TypedDict):
    mode: AccountingModeType
    defaultPurgeTimeInDays: NotRequired[int]

class AccountingTypeDef(TypedDict):
    mode: AccountingModeType
    defaultPurgeTimeInDays: NotRequired[int]

class SlurmCustomSettingTypeDef(TypedDict):
    parameterName: str
    parameterValue: str

class SlurmAuthKeyTypeDef(TypedDict):
    secretArn: str
    secretVersion: str

ClusterSummaryTypeDef = TypedDict(
    "ClusterSummaryTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "status": ClusterStatusType,
    },
)
EndpointTypeDef = TypedDict(
    "EndpointTypeDef",
    {
        "type": EndpointTypeType,
        "privateIpAddress": str,
        "port": str,
        "publicIpAddress": NotRequired[str],
        "ipv6Address": NotRequired[str],
    },
)

class ErrorInfoTypeDef(TypedDict):
    code: NotRequired[str]
    message: NotRequired[str]

class NetworkingTypeDef(TypedDict):
    subnetIds: NotRequired[List[str]]
    securityGroupIds: NotRequired[List[str]]
    networkType: NotRequired[NetworkTypeType]

SchedulerTypeDef = TypedDict(
    "SchedulerTypeDef",
    {
        "type": Literal["SLURM"],
        "version": str,
    },
)

class ComputeNodeGroupConfigurationTypeDef(TypedDict):
    computeNodeGroupId: NotRequired[str]

ComputeNodeGroupSummaryTypeDef = TypedDict(
    "ComputeNodeGroupSummaryTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "clusterId": str,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "status": ComputeNodeGroupStatusType,
    },
)
CustomLaunchTemplateTypeDef = TypedDict(
    "CustomLaunchTemplateTypeDef",
    {
        "id": str,
        "version": str,
    },
)

class InstanceConfigTypeDef(TypedDict):
    instanceType: NotRequired[str]

class ScalingConfigurationTypeDef(TypedDict):
    minInstanceCount: int
    maxInstanceCount: int

class SpotOptionsTypeDef(TypedDict):
    allocationStrategy: NotRequired[SpotAllocationStrategyType]

class NetworkingRequestTypeDef(TypedDict):
    subnetIds: NotRequired[Sequence[str]]
    securityGroupIds: NotRequired[Sequence[str]]
    networkType: NotRequired[NetworkTypeType]

SchedulerRequestTypeDef = TypedDict(
    "SchedulerRequestTypeDef",
    {
        "type": Literal["SLURM"],
        "version": str,
    },
)

class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]

class ScalingConfigurationRequestTypeDef(TypedDict):
    minInstanceCount: int
    maxInstanceCount: int

class DeleteClusterRequestTypeDef(TypedDict):
    clusterIdentifier: str
    clientToken: NotRequired[str]

class DeleteComputeNodeGroupRequestTypeDef(TypedDict):
    clusterIdentifier: str
    computeNodeGroupIdentifier: str
    clientToken: NotRequired[str]

class DeleteQueueRequestTypeDef(TypedDict):
    clusterIdentifier: str
    queueIdentifier: str
    clientToken: NotRequired[str]

class GetClusterRequestTypeDef(TypedDict):
    clusterIdentifier: str

class GetComputeNodeGroupRequestTypeDef(TypedDict):
    clusterIdentifier: str
    computeNodeGroupIdentifier: str

class GetQueueRequestTypeDef(TypedDict):
    clusterIdentifier: str
    queueIdentifier: str

class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]

class ListClustersRequestTypeDef(TypedDict):
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ListComputeNodeGroupsRequestTypeDef(TypedDict):
    clusterIdentifier: str
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ListQueuesRequestTypeDef(TypedDict):
    clusterIdentifier: str
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

QueueSummaryTypeDef = TypedDict(
    "QueueSummaryTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "clusterId": str,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "status": QueueStatusType,
    },
)

class ListTagsForResourceRequestTypeDef(TypedDict):
    resourceArn: str

class RegisterComputeNodeGroupInstanceRequestTypeDef(TypedDict):
    clusterIdentifier: str
    bootstrapId: str

class TagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tags: Mapping[str, str]

class UntagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tagKeys: Sequence[str]

class UpdateAccountingRequestTypeDef(TypedDict):
    defaultPurgeTimeInDays: NotRequired[int]
    mode: NotRequired[AccountingModeType]

class ClusterSlurmConfigurationRequestTypeDef(TypedDict):
    scaleDownIdleTimeInSeconds: NotRequired[int]
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]
    accounting: NotRequired[AccountingRequestTypeDef]

class ComputeNodeGroupSlurmConfigurationRequestTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]

class ComputeNodeGroupSlurmConfigurationTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[List[SlurmCustomSettingTypeDef]]

class QueueSlurmConfigurationRequestTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]

class QueueSlurmConfigurationTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[List[SlurmCustomSettingTypeDef]]

class UpdateComputeNodeGroupSlurmConfigurationRequestTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]

class UpdateQueueSlurmConfigurationRequestTypeDef(TypedDict):
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]

class ClusterSlurmConfigurationTypeDef(TypedDict):
    scaleDownIdleTimeInSeconds: NotRequired[int]
    slurmCustomSettings: NotRequired[List[SlurmCustomSettingTypeDef]]
    authKey: NotRequired[SlurmAuthKeyTypeDef]
    accounting: NotRequired[AccountingTypeDef]

class EmptyResponseMetadataTypeDef(TypedDict):
    ResponseMetadata: ResponseMetadataTypeDef

class ListClustersResponseTypeDef(TypedDict):
    clusters: List[ClusterSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ListComputeNodeGroupsResponseTypeDef(TypedDict):
    computeNodeGroups: List[ComputeNodeGroupSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ListTagsForResourceResponseTypeDef(TypedDict):
    tags: Dict[str, str]
    ResponseMetadata: ResponseMetadataTypeDef

class RegisterComputeNodeGroupInstanceResponseTypeDef(TypedDict):
    nodeID: str
    sharedSecret: str
    endpoints: List[EndpointTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class ListClustersRequestPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListComputeNodeGroupsRequestPaginateTypeDef(TypedDict):
    clusterIdentifier: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListQueuesRequestPaginateTypeDef(TypedDict):
    clusterIdentifier: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListQueuesResponseTypeDef(TypedDict):
    queues: List[QueueSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class UpdateClusterSlurmConfigurationRequestTypeDef(TypedDict):
    scaleDownIdleTimeInSeconds: NotRequired[int]
    slurmCustomSettings: NotRequired[Sequence[SlurmCustomSettingTypeDef]]
    accounting: NotRequired[UpdateAccountingRequestTypeDef]

class CreateClusterRequestTypeDef(TypedDict):
    clusterName: str
    scheduler: SchedulerRequestTypeDef
    size: SizeType
    networking: NetworkingRequestTypeDef
    slurmConfiguration: NotRequired[ClusterSlurmConfigurationRequestTypeDef]
    clientToken: NotRequired[str]
    tags: NotRequired[Mapping[str, str]]

class CreateComputeNodeGroupRequestTypeDef(TypedDict):
    clusterIdentifier: str
    computeNodeGroupName: str
    subnetIds: Sequence[str]
    customLaunchTemplate: CustomLaunchTemplateTypeDef
    iamInstanceProfileArn: str
    scalingConfiguration: ScalingConfigurationRequestTypeDef
    instanceConfigs: Sequence[InstanceConfigTypeDef]
    amiId: NotRequired[str]
    purchaseOption: NotRequired[PurchaseOptionType]
    spotOptions: NotRequired[SpotOptionsTypeDef]
    slurmConfiguration: NotRequired[ComputeNodeGroupSlurmConfigurationRequestTypeDef]
    clientToken: NotRequired[str]
    tags: NotRequired[Mapping[str, str]]

ComputeNodeGroupTypeDef = TypedDict(
    "ComputeNodeGroupTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "clusterId": str,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "status": ComputeNodeGroupStatusType,
        "subnetIds": List[str],
        "customLaunchTemplate": CustomLaunchTemplateTypeDef,
        "iamInstanceProfileArn": str,
        "scalingConfiguration": ScalingConfigurationTypeDef,
        "instanceConfigs": List[InstanceConfigTypeDef],
        "amiId": NotRequired[str],
        "purchaseOption": NotRequired[PurchaseOptionType],
        "spotOptions": NotRequired[SpotOptionsTypeDef],
        "slurmConfiguration": NotRequired[ComputeNodeGroupSlurmConfigurationTypeDef],
        "errorInfo": NotRequired[List[ErrorInfoTypeDef]],
    },
)

class CreateQueueRequestTypeDef(TypedDict):
    clusterIdentifier: str
    queueName: str
    computeNodeGroupConfigurations: NotRequired[Sequence[ComputeNodeGroupConfigurationTypeDef]]
    slurmConfiguration: NotRequired[QueueSlurmConfigurationRequestTypeDef]
    clientToken: NotRequired[str]
    tags: NotRequired[Mapping[str, str]]

QueueTypeDef = TypedDict(
    "QueueTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "clusterId": str,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "status": QueueStatusType,
        "computeNodeGroupConfigurations": List[ComputeNodeGroupConfigurationTypeDef],
        "slurmConfiguration": NotRequired[QueueSlurmConfigurationTypeDef],
        "errorInfo": NotRequired[List[ErrorInfoTypeDef]],
    },
)

class UpdateComputeNodeGroupRequestTypeDef(TypedDict):
    clusterIdentifier: str
    computeNodeGroupIdentifier: str
    amiId: NotRequired[str]
    subnetIds: NotRequired[Sequence[str]]
    customLaunchTemplate: NotRequired[CustomLaunchTemplateTypeDef]
    purchaseOption: NotRequired[PurchaseOptionType]
    spotOptions: NotRequired[SpotOptionsTypeDef]
    scalingConfiguration: NotRequired[ScalingConfigurationRequestTypeDef]
    iamInstanceProfileArn: NotRequired[str]
    slurmConfiguration: NotRequired[UpdateComputeNodeGroupSlurmConfigurationRequestTypeDef]
    clientToken: NotRequired[str]

class UpdateQueueRequestTypeDef(TypedDict):
    clusterIdentifier: str
    queueIdentifier: str
    computeNodeGroupConfigurations: NotRequired[Sequence[ComputeNodeGroupConfigurationTypeDef]]
    slurmConfiguration: NotRequired[UpdateQueueSlurmConfigurationRequestTypeDef]
    clientToken: NotRequired[str]

ClusterTypeDef = TypedDict(
    "ClusterTypeDef",
    {
        "name": str,
        "id": str,
        "arn": str,
        "status": ClusterStatusType,
        "createdAt": datetime,
        "modifiedAt": datetime,
        "scheduler": SchedulerTypeDef,
        "size": SizeType,
        "networking": NetworkingTypeDef,
        "slurmConfiguration": NotRequired[ClusterSlurmConfigurationTypeDef],
        "endpoints": NotRequired[List[EndpointTypeDef]],
        "errorInfo": NotRequired[List[ErrorInfoTypeDef]],
    },
)

class UpdateClusterRequestTypeDef(TypedDict):
    clusterIdentifier: str
    clientToken: NotRequired[str]
    slurmConfiguration: NotRequired[UpdateClusterSlurmConfigurationRequestTypeDef]

class CreateComputeNodeGroupResponseTypeDef(TypedDict):
    computeNodeGroup: ComputeNodeGroupTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GetComputeNodeGroupResponseTypeDef(TypedDict):
    computeNodeGroup: ComputeNodeGroupTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class UpdateComputeNodeGroupResponseTypeDef(TypedDict):
    computeNodeGroup: ComputeNodeGroupTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class CreateQueueResponseTypeDef(TypedDict):
    queue: QueueTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GetQueueResponseTypeDef(TypedDict):
    queue: QueueTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class UpdateQueueResponseTypeDef(TypedDict):
    queue: QueueTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class CreateClusterResponseTypeDef(TypedDict):
    cluster: ClusterTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GetClusterResponseTypeDef(TypedDict):
    cluster: ClusterTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class UpdateClusterResponseTypeDef(TypedDict):
    cluster: ClusterTypeDef
    ResponseMetadata: ResponseMetadataTypeDef
