"""
Type annotations for inspector2 service literal definitions.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_inspector2/literals/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from types_boto3_inspector2.literals import AccountSortByType

    data: AccountSortByType = "ALL"
    ```
"""

import sys

if sys.version_info >= (3, 12):
    from typing import Literal
else:
    from typing_extensions import Literal

__all__ = (
    "AccountSortByType",
    "AggregationFindingTypeType",
    "AggregationResourceTypeType",
    "AggregationTypeType",
    "AmiSortByType",
    "ArchitectureType",
    "AssociationResultStatusCodeType",
    "AwsEcrContainerSortByType",
    "CisFindingStatusComparisonType",
    "CisFindingStatusType",
    "CisReportFormatType",
    "CisReportStatusType",
    "CisResultStatusComparisonType",
    "CisResultStatusType",
    "CisRuleStatusType",
    "CisScanConfigurationsSortByType",
    "CisScanResultDetailsSortByType",
    "CisScanResultsAggregatedByChecksSortByType",
    "CisScanResultsAggregatedByTargetResourceSortByType",
    "CisScanStatusComparisonType",
    "CisScanStatusType",
    "CisSecurityLevelComparisonType",
    "CisSecurityLevelType",
    "CisSortOrderType",
    "CisStringComparisonType",
    "CisTargetStatusComparisonType",
    "CisTargetStatusReasonType",
    "CisTargetStatusType",
    "CodeRepositoryProviderTypeType",
    "CodeRepositorySortByType",
    "CodeScanStatusType",
    "CodeSnippetErrorCodeType",
    "ConfigurationLevelType",
    "ContinuousIntegrationScanEventType",
    "CoverageMapComparisonType",
    "CoverageResourceTypeType",
    "CoverageStringComparisonType",
    "CurrencyType",
    "DayType",
    "DelegatedAdminStatusType",
    "Ec2DeepInspectionStatusType",
    "Ec2InstanceSortByType",
    "Ec2PlatformType",
    "Ec2ScanModeStatusType",
    "Ec2ScanModeType",
    "EcrPullDateRescanDurationType",
    "EcrPullDateRescanModeType",
    "EcrRescanDurationStatusType",
    "EcrRescanDurationType",
    "EcrScanFrequencyType",
    "ErrorCodeType",
    "ExploitAvailableType",
    "ExternalReportStatusType",
    "FilterActionType",
    "FindingDetailsErrorCodeType",
    "FindingStatusType",
    "FindingTypeSortByType",
    "FindingTypeType",
    "FixAvailableType",
    "FreeTrialInfoErrorCodeType",
    "FreeTrialStatusType",
    "FreeTrialTypeType",
    "GetCisScanResultDetailsPaginatorName",
    "GetClustersForImagePaginatorName",
    "GroupKeyType",
    "ImageLayerSortByType",
    "Inspector2ServiceName",
    "IntegrationStatusType",
    "IntegrationTypeType",
    "LambdaFunctionSortByType",
    "LambdaLayerSortByType",
    "ListAccountPermissionsPaginatorName",
    "ListCisScanConfigurationsPaginatorName",
    "ListCisScanResultsAggregatedByChecksPaginatorName",
    "ListCisScanResultsAggregatedByTargetResourcePaginatorName",
    "ListCisScansDetailLevelType",
    "ListCisScansPaginatorName",
    "ListCisScansSortByType",
    "ListCoveragePaginatorName",
    "ListCoverageStatisticsPaginatorName",
    "ListDelegatedAdminAccountsPaginatorName",
    "ListFiltersPaginatorName",
    "ListFindingAggregationsPaginatorName",
    "ListFindingsPaginatorName",
    "ListMembersPaginatorName",
    "ListUsageTotalsPaginatorName",
    "MapComparisonType",
    "NetworkProtocolType",
    "OperationType",
    "PackageManagerType",
    "PackageSortByType",
    "PackageTypeType",
    "PaginatorName",
    "PeriodicScanFrequencyType",
    "ProjectSelectionScopeType",
    "RegionName",
    "RelationshipStatusType",
    "ReportFormatType",
    "ReportingErrorCodeType",
    "RepositorySortByType",
    "ResourceMapComparisonType",
    "ResourceScanTypeType",
    "ResourceServiceName",
    "ResourceStringComparisonType",
    "ResourceTypeType",
    "RuleSetCategoryType",
    "RuntimeType",
    "SbomReportFormatType",
    "ScanModeType",
    "ScanStatusCodeType",
    "ScanStatusReasonType",
    "ScanTypeType",
    "SearchVulnerabilitiesPaginatorName",
    "ServiceName",
    "ServiceType",
    "SeverityType",
    "SortFieldType",
    "SortOrderType",
    "StatusType",
    "StopCisSessionStatusType",
    "StringComparisonType",
    "TagComparisonType",
    "TitleSortByType",
    "UsageTypeType",
    "VulnerabilitySourceType",
)

AccountSortByType = Literal["ALL", "CRITICAL", "HIGH"]
AggregationFindingTypeType = Literal[
    "CODE_VULNERABILITY", "NETWORK_REACHABILITY", "PACKAGE_VULNERABILITY"
]
AggregationResourceTypeType = Literal[
    "AWS_EC2_INSTANCE", "AWS_ECR_CONTAINER_IMAGE", "AWS_LAMBDA_FUNCTION", "CODE_REPOSITORY"
]
AggregationTypeType = Literal[
    "ACCOUNT",
    "AMI",
    "AWS_EC2_INSTANCE",
    "AWS_ECR_CONTAINER",
    "AWS_LAMBDA_FUNCTION",
    "CODE_REPOSITORY",
    "FINDING_TYPE",
    "IMAGE_LAYER",
    "LAMBDA_LAYER",
    "PACKAGE",
    "REPOSITORY",
    "TITLE",
]
AmiSortByType = Literal["AFFECTED_INSTANCES", "ALL", "CRITICAL", "HIGH"]
ArchitectureType = Literal["ARM64", "X86_64"]
AssociationResultStatusCodeType = Literal[
    "ACCESS_DENIED",
    "INTERNAL_ERROR",
    "INVALID_INPUT",
    "QUOTA_EXCEEDED",
    "RESOURCE_NOT_FOUND",
    "SCAN_CONFIGURATION_NOT_FOUND",
]
AwsEcrContainerSortByType = Literal["ALL", "CRITICAL", "HIGH"]
CisFindingStatusComparisonType = Literal["EQUALS"]
CisFindingStatusType = Literal["FAILED", "PASSED", "SKIPPED"]
CisReportFormatType = Literal["CSV", "PDF"]
CisReportStatusType = Literal["FAILED", "IN_PROGRESS", "SUCCEEDED"]
CisResultStatusComparisonType = Literal["EQUALS"]
CisResultStatusType = Literal["FAILED", "PASSED", "SKIPPED"]
CisRuleStatusType = Literal[
    "ERROR", "FAILED", "INFORMATIONAL", "NOT_APPLICABLE", "NOT_EVALUATED", "PASSED", "UNKNOWN"
]
CisScanConfigurationsSortByType = Literal["SCAN_CONFIGURATION_ARN", "SCAN_NAME"]
CisScanResultDetailsSortByType = Literal["CHECK_ID", "STATUS"]
CisScanResultsAggregatedByChecksSortByType = Literal[
    "CHECK_ID", "FAILED_COUNTS", "PLATFORM", "SECURITY_LEVEL", "TITLE"
]
CisScanResultsAggregatedByTargetResourceSortByType = Literal[
    "ACCOUNT_ID",
    "FAILED_COUNTS",
    "PLATFORM",
    "RESOURCE_ID",
    "TARGET_STATUS",
    "TARGET_STATUS_REASON",
]
CisScanStatusComparisonType = Literal["EQUALS"]
CisScanStatusType = Literal["CANCELLED", "COMPLETED", "FAILED", "IN_PROGRESS"]
CisSecurityLevelComparisonType = Literal["EQUALS"]
CisSecurityLevelType = Literal["LEVEL_1", "LEVEL_2"]
CisSortOrderType = Literal["ASC", "DESC"]
CisStringComparisonType = Literal["EQUALS", "NOT_EQUALS", "PREFIX"]
CisTargetStatusComparisonType = Literal["EQUALS"]
CisTargetStatusReasonType = Literal["SCAN_IN_PROGRESS", "SSM_UNMANAGED", "UNSUPPORTED_OS"]
CisTargetStatusType = Literal["CANCELLED", "COMPLETED", "TIMED_OUT"]
CodeRepositoryProviderTypeType = Literal["GITHUB", "GITLAB_SELF_MANAGED"]
CodeRepositorySortByType = Literal["ALL", "CRITICAL", "HIGH"]
CodeScanStatusType = Literal["FAILED", "IN_PROGRESS", "SKIPPED", "SUCCESSFUL"]
CodeSnippetErrorCodeType = Literal[
    "ACCESS_DENIED", "CODE_SNIPPET_NOT_FOUND", "INTERNAL_ERROR", "INVALID_INPUT"
]
ConfigurationLevelType = Literal["ACCOUNT", "ORGANIZATION"]
ContinuousIntegrationScanEventType = Literal["PULL_REQUEST", "PUSH"]
CoverageMapComparisonType = Literal["EQUALS"]
CoverageResourceTypeType = Literal[
    "AWS_EC2_INSTANCE",
    "AWS_ECR_CONTAINER_IMAGE",
    "AWS_ECR_REPOSITORY",
    "AWS_LAMBDA_FUNCTION",
    "CODE_REPOSITORY",
]
CoverageStringComparisonType = Literal["EQUALS", "NOT_EQUALS"]
CurrencyType = Literal["USD"]
DayType = Literal["FRI", "MON", "SAT", "SUN", "THU", "TUE", "WED"]
DelegatedAdminStatusType = Literal["DISABLE_IN_PROGRESS", "ENABLED"]
Ec2DeepInspectionStatusType = Literal["ACTIVATED", "DEACTIVATED", "FAILED", "PENDING"]
Ec2InstanceSortByType = Literal["ALL", "CRITICAL", "HIGH", "NETWORK_FINDINGS"]
Ec2PlatformType = Literal["LINUX", "MACOS", "UNKNOWN", "WINDOWS"]
Ec2ScanModeStatusType = Literal["PENDING", "SUCCESS"]
Ec2ScanModeType = Literal["EC2_HYBRID", "EC2_SSM_AGENT_BASED"]
EcrPullDateRescanDurationType = Literal["DAYS_14", "DAYS_180", "DAYS_30", "DAYS_60", "DAYS_90"]
EcrPullDateRescanModeType = Literal["LAST_IN_USE_AT", "LAST_PULL_DATE"]
EcrRescanDurationStatusType = Literal["FAILED", "PENDING", "SUCCESS"]
EcrRescanDurationType = Literal["DAYS_14", "DAYS_180", "DAYS_30", "DAYS_60", "DAYS_90", "LIFETIME"]
EcrScanFrequencyType = Literal["CONTINUOUS_SCAN", "MANUAL", "SCAN_ON_PUSH"]
ErrorCodeType = Literal[
    "ACCESS_DENIED",
    "ACCOUNT_IS_ISOLATED",
    "ALREADY_ENABLED",
    "DISABLE_IN_PROGRESS",
    "DISASSOCIATE_ALL_MEMBERS",
    "EC2_SSM_ASSOCIATION_VERSION_LIMIT_EXCEEDED",
    "EC2_SSM_RESOURCE_DATA_SYNC_LIMIT_EXCEEDED",
    "ENABLE_IN_PROGRESS",
    "EVENTBRIDGE_THROTTLED",
    "EVENTBRIDGE_UNAVAILABLE",
    "INTERNAL_ERROR",
    "RESOURCE_NOT_FOUND",
    "RESOURCE_SCAN_NOT_DISABLED",
    "SSM_THROTTLED",
    "SSM_UNAVAILABLE",
    "SUSPEND_IN_PROGRESS",
]
ExploitAvailableType = Literal["NO", "YES"]
ExternalReportStatusType = Literal["CANCELLED", "FAILED", "IN_PROGRESS", "SUCCEEDED"]
FilterActionType = Literal["NONE", "SUPPRESS"]
FindingDetailsErrorCodeType = Literal[
    "ACCESS_DENIED", "FINDING_DETAILS_NOT_FOUND", "INTERNAL_ERROR", "INVALID_INPUT"
]
FindingStatusType = Literal["ACTIVE", "CLOSED", "SUPPRESSED"]
FindingTypeSortByType = Literal["ALL", "CRITICAL", "HIGH"]
FindingTypeType = Literal["CODE_VULNERABILITY", "NETWORK_REACHABILITY", "PACKAGE_VULNERABILITY"]
FixAvailableType = Literal["NO", "PARTIAL", "YES"]
FreeTrialInfoErrorCodeType = Literal["ACCESS_DENIED", "INTERNAL_ERROR"]
FreeTrialStatusType = Literal["ACTIVE", "INACTIVE"]
FreeTrialTypeType = Literal["CODE_REPOSITORY", "EC2", "ECR", "LAMBDA", "LAMBDA_CODE"]
GetCisScanResultDetailsPaginatorName = Literal["get_cis_scan_result_details"]
GetClustersForImagePaginatorName = Literal["get_clusters_for_image"]
GroupKeyType = Literal[
    "ACCOUNT_ID", "ECR_REPOSITORY_NAME", "RESOURCE_TYPE", "SCAN_STATUS_CODE", "SCAN_STATUS_REASON"
]
ImageLayerSortByType = Literal["ALL", "CRITICAL", "HIGH"]
IntegrationStatusType = Literal["ACTIVE", "DISABLING", "INACTIVE", "IN_PROGRESS", "PENDING"]
IntegrationTypeType = Literal["GITHUB", "GITLAB_SELF_MANAGED"]
LambdaFunctionSortByType = Literal["ALL", "CRITICAL", "HIGH"]
LambdaLayerSortByType = Literal["ALL", "CRITICAL", "HIGH"]
ListAccountPermissionsPaginatorName = Literal["list_account_permissions"]
ListCisScanConfigurationsPaginatorName = Literal["list_cis_scan_configurations"]
ListCisScanResultsAggregatedByChecksPaginatorName = Literal[
    "list_cis_scan_results_aggregated_by_checks"
]
ListCisScanResultsAggregatedByTargetResourcePaginatorName = Literal[
    "list_cis_scan_results_aggregated_by_target_resource"
]
ListCisScansDetailLevelType = Literal["MEMBER", "ORGANIZATION"]
ListCisScansPaginatorName = Literal["list_cis_scans"]
ListCisScansSortByType = Literal["FAILED_CHECKS", "SCAN_START_DATE", "SCHEDULED_BY", "STATUS"]
ListCoveragePaginatorName = Literal["list_coverage"]
ListCoverageStatisticsPaginatorName = Literal["list_coverage_statistics"]
ListDelegatedAdminAccountsPaginatorName = Literal["list_delegated_admin_accounts"]
ListFiltersPaginatorName = Literal["list_filters"]
ListFindingAggregationsPaginatorName = Literal["list_finding_aggregations"]
ListFindingsPaginatorName = Literal["list_findings"]
ListMembersPaginatorName = Literal["list_members"]
ListUsageTotalsPaginatorName = Literal["list_usage_totals"]
MapComparisonType = Literal["EQUALS"]
NetworkProtocolType = Literal["TCP", "UDP"]
OperationType = Literal[
    "DISABLE_REPOSITORY", "DISABLE_SCANNING", "ENABLE_REPOSITORY", "ENABLE_SCANNING"
]
PackageManagerType = Literal[
    "BUNDLER",
    "CARGO",
    "COMPOSER",
    "DOTNET_CORE",
    "GEMSPEC",
    "GOBINARY",
    "GOMOD",
    "JAR",
    "NODEPKG",
    "NPM",
    "NUGET",
    "OS",
    "PIP",
    "PIPENV",
    "POETRY",
    "POM",
    "PYTHONPKG",
    "YARN",
]
PackageSortByType = Literal["ALL", "CRITICAL", "HIGH"]
PackageTypeType = Literal["IMAGE", "ZIP"]
PeriodicScanFrequencyType = Literal["MONTHLY", "NEVER", "WEEKLY"]
ProjectSelectionScopeType = Literal["ALL"]
RelationshipStatusType = Literal[
    "ACCOUNT_SUSPENDED",
    "CANNOT_CREATE_DETECTOR_IN_ORG_MASTER",
    "CREATED",
    "DELETED",
    "DISABLED",
    "EMAIL_VERIFICATION_FAILED",
    "EMAIL_VERIFICATION_IN_PROGRESS",
    "ENABLED",
    "INVITED",
    "REGION_DISABLED",
    "REMOVED",
    "RESIGNED",
]
ReportFormatType = Literal["CSV", "JSON"]
ReportingErrorCodeType = Literal[
    "BUCKET_NOT_FOUND",
    "INCOMPATIBLE_BUCKET_REGION",
    "INTERNAL_ERROR",
    "INVALID_PERMISSIONS",
    "MALFORMED_KMS_KEY",
    "NO_FINDINGS_FOUND",
]
RepositorySortByType = Literal["AFFECTED_IMAGES", "ALL", "CRITICAL", "HIGH"]
ResourceMapComparisonType = Literal["EQUALS"]
ResourceScanTypeType = Literal["CODE_REPOSITORY", "EC2", "ECR", "LAMBDA", "LAMBDA_CODE"]
ResourceStringComparisonType = Literal["EQUALS", "NOT_EQUALS"]
ResourceTypeType = Literal[
    "AWS_EC2_INSTANCE",
    "AWS_ECR_CONTAINER_IMAGE",
    "AWS_ECR_REPOSITORY",
    "AWS_LAMBDA_FUNCTION",
    "CODE_REPOSITORY",
]
RuleSetCategoryType = Literal["IAC", "SAST", "SCA"]
RuntimeType = Literal[
    "DOTNETCORE_3_1",
    "DOTNET_6",
    "DOTNET_7",
    "GO_1_X",
    "JAVA_11",
    "JAVA_17",
    "JAVA_8",
    "JAVA_8_AL2",
    "NODEJS",
    "NODEJS_12_X",
    "NODEJS_14_X",
    "NODEJS_16_X",
    "NODEJS_18_X",
    "PYTHON_3_10",
    "PYTHON_3_11",
    "PYTHON_3_7",
    "PYTHON_3_8",
    "PYTHON_3_9",
    "RUBY_2_7",
    "RUBY_3_2",
    "UNSUPPORTED",
]
SbomReportFormatType = Literal["CYCLONEDX_1_4", "SPDX_2_3"]
ScanModeType = Literal["EC2_AGENTLESS", "EC2_SSM_AGENT_BASED"]
ScanStatusCodeType = Literal["ACTIVE", "INACTIVE"]
ScanStatusReasonType = Literal[
    "ACCESS_DENIED",
    "ACCESS_DENIED_TO_ENCRYPTION_KEY",
    "AGENTLESS_INSTANCE_COLLECTION_TIME_LIMIT_EXCEEDED",
    "AGENTLESS_INSTANCE_STORAGE_LIMIT_EXCEEDED",
    "DEEP_INSPECTION_COLLECTION_TIME_LIMIT_EXCEEDED",
    "DEEP_INSPECTION_DAILY_SSM_INVENTORY_LIMIT_EXCEEDED",
    "DEEP_INSPECTION_NO_INVENTORY",
    "DEEP_INSPECTION_PACKAGE_COLLECTION_LIMIT_EXCEEDED",
    "EC2_INSTANCE_STOPPED",
    "EXCLUDED_BY_TAG",
    "IMAGE_SIZE_EXCEEDED",
    "INTEGRATION_CONNECTION_LOST",
    "INTERNAL_ERROR",
    "NO_INVENTORY",
    "NO_RESOURCES_FOUND",
    "NO_SCAN_CONFIGURATION_ASSOCIATED",
    "PENDING_DISABLE",
    "PENDING_INITIAL_SCAN",
    "PENDING_REVIVAL_SCAN",
    "RESOURCE_TERMINATED",
    "SCAN_ELIGIBILITY_EXPIRED",
    "SCAN_FREQUENCY_MANUAL",
    "SCAN_FREQUENCY_SCAN_ON_PUSH",
    "SCAN_IN_PROGRESS",
    "STALE_INVENTORY",
    "SUCCESSFUL",
    "UNMANAGED_EC2_INSTANCE",
    "UNSUPPORTED_CONFIG_FILE",
    "UNSUPPORTED_LANGUAGE",
    "UNSUPPORTED_MEDIA_TYPE",
    "UNSUPPORTED_OS",
    "UNSUPPORTED_RUNTIME",
]
ScanTypeType = Literal["CODE", "NETWORK", "PACKAGE"]
SearchVulnerabilitiesPaginatorName = Literal["search_vulnerabilities"]
ServiceType = Literal["EC2", "ECR", "LAMBDA"]
SeverityType = Literal["CRITICAL", "HIGH", "INFORMATIONAL", "LOW", "MEDIUM", "UNTRIAGED"]
SortFieldType = Literal[
    "AWS_ACCOUNT_ID",
    "COMPONENT_TYPE",
    "ECR_IMAGE_PUSHED_AT",
    "ECR_IMAGE_REGISTRY",
    "ECR_IMAGE_REPOSITORY_NAME",
    "EPSS_SCORE",
    "FINDING_STATUS",
    "FINDING_TYPE",
    "FIRST_OBSERVED_AT",
    "INSPECTOR_SCORE",
    "LAST_OBSERVED_AT",
    "NETWORK_PROTOCOL",
    "RESOURCE_TYPE",
    "SEVERITY",
    "VENDOR_SEVERITY",
    "VULNERABILITY_ID",
    "VULNERABILITY_SOURCE",
]
SortOrderType = Literal["ASC", "DESC"]
StatusType = Literal["DISABLED", "DISABLING", "ENABLED", "ENABLING", "SUSPENDED", "SUSPENDING"]
StopCisSessionStatusType = Literal["FAILED", "INTERRUPTED", "SUCCESS", "UNSUPPORTED_OS"]
StringComparisonType = Literal["EQUALS", "NOT_EQUALS", "PREFIX"]
TagComparisonType = Literal["EQUALS"]
TitleSortByType = Literal["ALL", "CRITICAL", "HIGH"]
UsageTypeType = Literal[
    "CODE_REPOSITORY_IAC",
    "CODE_REPOSITORY_SAST",
    "CODE_REPOSITORY_SCA",
    "EC2_AGENTLESS_INSTANCE_HOURS",
    "EC2_INSTANCE_HOURS",
    "ECR_INITIAL_SCAN",
    "ECR_RESCAN",
    "LAMBDA_FUNCTION_CODE_HOURS",
    "LAMBDA_FUNCTION_HOURS",
]
VulnerabilitySourceType = Literal["NVD"]
Inspector2ServiceName = Literal["inspector2"]
ServiceName = Literal[
    "accessanalyzer",
    "account",
    "acm",
    "acm-pca",
    "aiops",
    "amp",
    "amplify",
    "amplifybackend",
    "amplifyuibuilder",
    "apigateway",
    "apigatewaymanagementapi",
    "apigatewayv2",
    "appconfig",
    "appconfigdata",
    "appfabric",
    "appflow",
    "appintegrations",
    "application-autoscaling",
    "application-insights",
    "application-signals",
    "applicationcostprofiler",
    "appmesh",
    "apprunner",
    "appstream",
    "appsync",
    "apptest",
    "arc-region-switch",
    "arc-zonal-shift",
    "artifact",
    "athena",
    "auditmanager",
    "autoscaling",
    "autoscaling-plans",
    "b2bi",
    "backup",
    "backup-gateway",
    "backupsearch",
    "batch",
    "bcm-dashboards",
    "bcm-data-exports",
    "bcm-pricing-calculator",
    "bcm-recommended-actions",
    "bedrock",
    "bedrock-agent",
    "bedrock-agent-runtime",
    "bedrock-agentcore",
    "bedrock-agentcore-control",
    "bedrock-data-automation",
    "bedrock-data-automation-runtime",
    "bedrock-runtime",
    "billing",
    "billingconductor",
    "braket",
    "budgets",
    "ce",
    "chatbot",
    "chime",
    "chime-sdk-identity",
    "chime-sdk-media-pipelines",
    "chime-sdk-meetings",
    "chime-sdk-messaging",
    "chime-sdk-voice",
    "cleanrooms",
    "cleanroomsml",
    "cloud9",
    "cloudcontrol",
    "clouddirectory",
    "cloudformation",
    "cloudfront",
    "cloudfront-keyvaluestore",
    "cloudhsm",
    "cloudhsmv2",
    "cloudsearch",
    "cloudsearchdomain",
    "cloudtrail",
    "cloudtrail-data",
    "cloudwatch",
    "codeartifact",
    "codebuild",
    "codecatalyst",
    "codecommit",
    "codeconnections",
    "codedeploy",
    "codeguru-reviewer",
    "codeguru-security",
    "codeguruprofiler",
    "codepipeline",
    "codestar-connections",
    "codestar-notifications",
    "cognito-identity",
    "cognito-idp",
    "cognito-sync",
    "comprehend",
    "comprehendmedical",
    "compute-optimizer",
    "config",
    "connect",
    "connect-contact-lens",
    "connectcampaigns",
    "connectcampaignsv2",
    "connectcases",
    "connectparticipant",
    "controlcatalog",
    "controltower",
    "cost-optimization-hub",
    "cur",
    "customer-profiles",
    "databrew",
    "dataexchange",
    "datapipeline",
    "datasync",
    "datazone",
    "dax",
    "deadline",
    "detective",
    "devicefarm",
    "devops-guru",
    "directconnect",
    "discovery",
    "dlm",
    "dms",
    "docdb",
    "docdb-elastic",
    "drs",
    "ds",
    "ds-data",
    "dsql",
    "dynamodb",
    "dynamodbstreams",
    "ebs",
    "ec2",
    "ec2-instance-connect",
    "ecr",
    "ecr-public",
    "ecs",
    "efs",
    "eks",
    "eks-auth",
    "elasticache",
    "elasticbeanstalk",
    "elastictranscoder",
    "elb",
    "elbv2",
    "emr",
    "emr-containers",
    "emr-serverless",
    "entityresolution",
    "es",
    "events",
    "evidently",
    "evs",
    "finspace",
    "finspace-data",
    "firehose",
    "fis",
    "fms",
    "forecast",
    "forecastquery",
    "frauddetector",
    "freetier",
    "fsx",
    "gamelift",
    "gameliftstreams",
    "geo-maps",
    "geo-places",
    "geo-routes",
    "glacier",
    "globalaccelerator",
    "glue",
    "grafana",
    "greengrass",
    "greengrassv2",
    "groundstation",
    "guardduty",
    "health",
    "healthlake",
    "iam",
    "identitystore",
    "imagebuilder",
    "importexport",
    "inspector",
    "inspector-scan",
    "inspector2",
    "internetmonitor",
    "invoicing",
    "iot",
    "iot-data",
    "iot-jobs-data",
    "iot-managed-integrations",
    "iotanalytics",
    "iotdeviceadvisor",
    "iotevents",
    "iotevents-data",
    "iotfleethub",
    "iotfleetwise",
    "iotsecuretunneling",
    "iotsitewise",
    "iotthingsgraph",
    "iottwinmaker",
    "iotwireless",
    "ivs",
    "ivs-realtime",
    "ivschat",
    "kafka",
    "kafkaconnect",
    "kendra",
    "kendra-ranking",
    "keyspaces",
    "keyspacesstreams",
    "kinesis",
    "kinesis-video-archived-media",
    "kinesis-video-media",
    "kinesis-video-signaling",
    "kinesis-video-webrtc-storage",
    "kinesisanalytics",
    "kinesisanalyticsv2",
    "kinesisvideo",
    "kms",
    "lakeformation",
    "lambda",
    "launch-wizard",
    "lex-models",
    "lex-runtime",
    "lexv2-models",
    "lexv2-runtime",
    "license-manager",
    "license-manager-linux-subscriptions",
    "license-manager-user-subscriptions",
    "lightsail",
    "location",
    "logs",
    "lookoutequipment",
    "lookoutmetrics",
    "lookoutvision",
    "m2",
    "machinelearning",
    "macie2",
    "mailmanager",
    "managedblockchain",
    "managedblockchain-query",
    "marketplace-agreement",
    "marketplace-catalog",
    "marketplace-deployment",
    "marketplace-entitlement",
    "marketplace-reporting",
    "marketplacecommerceanalytics",
    "mediaconnect",
    "mediaconvert",
    "medialive",
    "mediapackage",
    "mediapackage-vod",
    "mediapackagev2",
    "mediastore",
    "mediastore-data",
    "mediatailor",
    "medical-imaging",
    "memorydb",
    "meteringmarketplace",
    "mgh",
    "mgn",
    "migration-hub-refactor-spaces",
    "migrationhub-config",
    "migrationhuborchestrator",
    "migrationhubstrategy",
    "mpa",
    "mq",
    "mturk",
    "mwaa",
    "neptune",
    "neptune-graph",
    "neptunedata",
    "network-firewall",
    "networkflowmonitor",
    "networkmanager",
    "networkmonitor",
    "notifications",
    "notificationscontacts",
    "oam",
    "observabilityadmin",
    "odb",
    "omics",
    "opensearch",
    "opensearchserverless",
    "organizations",
    "osis",
    "outposts",
    "panorama",
    "partnercentral-selling",
    "payment-cryptography",
    "payment-cryptography-data",
    "pca-connector-ad",
    "pca-connector-scep",
    "pcs",
    "personalize",
    "personalize-events",
    "personalize-runtime",
    "pi",
    "pinpoint",
    "pinpoint-email",
    "pinpoint-sms-voice",
    "pinpoint-sms-voice-v2",
    "pipes",
    "polly",
    "pricing",
    "proton",
    "qapps",
    "qbusiness",
    "qconnect",
    "qldb",
    "qldb-session",
    "quicksight",
    "ram",
    "rbin",
    "rds",
    "rds-data",
    "redshift",
    "redshift-data",
    "redshift-serverless",
    "rekognition",
    "repostspace",
    "resiliencehub",
    "resource-explorer-2",
    "resource-groups",
    "resourcegroupstaggingapi",
    "robomaker",
    "rolesanywhere",
    "route53",
    "route53-recovery-cluster",
    "route53-recovery-control-config",
    "route53-recovery-readiness",
    "route53domains",
    "route53profiles",
    "route53resolver",
    "rtbfabric",
    "rum",
    "s3",
    "s3control",
    "s3outposts",
    "s3tables",
    "s3vectors",
    "sagemaker",
    "sagemaker-a2i-runtime",
    "sagemaker-edge",
    "sagemaker-featurestore-runtime",
    "sagemaker-geospatial",
    "sagemaker-metrics",
    "sagemaker-runtime",
    "savingsplans",
    "scheduler",
    "schemas",
    "sdb",
    "secretsmanager",
    "security-ir",
    "securityhub",
    "securitylake",
    "serverlessrepo",
    "service-quotas",
    "servicecatalog",
    "servicecatalog-appregistry",
    "servicediscovery",
    "ses",
    "sesv2",
    "shield",
    "signer",
    "simspaceweaver",
    "snow-device-management",
    "snowball",
    "sns",
    "socialmessaging",
    "sqs",
    "ssm",
    "ssm-contacts",
    "ssm-guiconnect",
    "ssm-incidents",
    "ssm-quicksetup",
    "ssm-sap",
    "sso",
    "sso-admin",
    "sso-oidc",
    "stepfunctions",
    "storagegateway",
    "sts",
    "supplychain",
    "support",
    "support-app",
    "swf",
    "synthetics",
    "taxsettings",
    "textract",
    "timestream-influxdb",
    "timestream-query",
    "timestream-write",
    "tnb",
    "transcribe",
    "transfer",
    "translate",
    "trustedadvisor",
    "verifiedpermissions",
    "voice-id",
    "vpc-lattice",
    "waf",
    "waf-regional",
    "wafv2",
    "wellarchitected",
    "wisdom",
    "workdocs",
    "workmail",
    "workmailmessageflow",
    "workspaces",
    "workspaces-instances",
    "workspaces-thin-client",
    "workspaces-web",
    "xray",
]
ResourceServiceName = Literal[
    "cloudformation", "cloudwatch", "dynamodb", "ec2", "glacier", "iam", "s3", "sns", "sqs"
]
PaginatorName = Literal[
    "get_cis_scan_result_details",
    "get_clusters_for_image",
    "list_account_permissions",
    "list_cis_scan_configurations",
    "list_cis_scan_results_aggregated_by_checks",
    "list_cis_scan_results_aggregated_by_target_resource",
    "list_cis_scans",
    "list_coverage",
    "list_coverage_statistics",
    "list_delegated_admin_accounts",
    "list_filters",
    "list_finding_aggregations",
    "list_findings",
    "list_members",
    "list_usage_totals",
    "search_vulnerabilities",
]
RegionName = Literal[
    "af-south-1",
    "ap-east-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-south-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "ap-southeast-5",
    "ap-southeast-7",
    "ca-central-1",
    "ca-west-1",
    "eu-central-1",
    "eu-central-2",
    "eu-north-1",
    "eu-south-1",
    "eu-south-2",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "il-central-1",
    "me-central-1",
    "me-south-1",
    "mx-central-1",
    "sa-east-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
]
