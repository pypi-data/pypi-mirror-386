"""
Type annotations for iotsitewise service literal definitions.

[Documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotsitewise/literals/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from mypy_boto3_iotsitewise.literals import AggregateTypeType

    data: AggregateTypeType = "AVERAGE"
    ```
"""

import sys

if sys.version_info >= (3, 12):
    from typing import Literal
else:
    from typing_extensions import Literal


__all__ = (
    "AggregateTypeType",
    "AssetActiveWaiterName",
    "AssetErrorCodeType",
    "AssetModelActiveWaiterName",
    "AssetModelNotExistsWaiterName",
    "AssetModelStateType",
    "AssetModelTypeType",
    "AssetModelVersionTypeType",
    "AssetNotExistsWaiterName",
    "AssetRelationshipTypeType",
    "AssetStateType",
    "AuthModeType",
    "BatchEntryCompletionStatusType",
    "BatchGetAssetPropertyAggregatesErrorCodeType",
    "BatchGetAssetPropertyValueErrorCodeType",
    "BatchGetAssetPropertyValueHistoryErrorCodeType",
    "BatchPutAssetPropertyValueErrorCodeType",
    "CapabilitySyncStatusType",
    "ColumnNameType",
    "ComputationModelStateType",
    "ComputationModelTypeType",
    "ComputeLocationType",
    "ConfigurationStateType",
    "CoreDeviceOperatingSystemType",
    "DatasetSourceFormatType",
    "DatasetSourceTypeType",
    "DatasetStateType",
    "DetailedErrorCodeType",
    "DisassociatedDataStorageStateType",
    "EncryptionTypeType",
    "ErrorCodeType",
    "ExecuteQueryPaginatorName",
    "ExecutionStateType",
    "ForwardingConfigStateType",
    "GetAssetPropertyAggregatesPaginatorName",
    "GetAssetPropertyValueHistoryPaginatorName",
    "GetInterpolatedAssetPropertyValuesPaginatorName",
    "IdentityTypeType",
    "ImageFileTypeType",
    "IoTSiteWiseServiceName",
    "JobStatusType",
    "ListAccessPoliciesPaginatorName",
    "ListActionsPaginatorName",
    "ListAssetModelCompositeModelsPaginatorName",
    "ListAssetModelPropertiesFilterType",
    "ListAssetModelPropertiesPaginatorName",
    "ListAssetModelsPaginatorName",
    "ListAssetPropertiesFilterType",
    "ListAssetPropertiesPaginatorName",
    "ListAssetRelationshipsPaginatorName",
    "ListAssetsFilterType",
    "ListAssetsPaginatorName",
    "ListAssociatedAssetsPaginatorName",
    "ListBulkImportJobsFilterType",
    "ListBulkImportJobsPaginatorName",
    "ListCompositionRelationshipsPaginatorName",
    "ListComputationModelDataBindingUsagesPaginatorName",
    "ListComputationModelResolveToResourcesPaginatorName",
    "ListComputationModelsPaginatorName",
    "ListDashboardsPaginatorName",
    "ListDatasetsPaginatorName",
    "ListExecutionsPaginatorName",
    "ListGatewaysPaginatorName",
    "ListInterfaceRelationshipsPaginatorName",
    "ListPortalsPaginatorName",
    "ListProjectAssetsPaginatorName",
    "ListProjectsPaginatorName",
    "ListTimeSeriesPaginatorName",
    "ListTimeSeriesTypeType",
    "LoggingLevelType",
    "MonitorErrorCodeType",
    "PaginatorName",
    "PermissionType",
    "PortalActiveWaiterName",
    "PortalNotExistsWaiterName",
    "PortalStateType",
    "PortalTypeType",
    "PropertyDataTypeType",
    "PropertyNotificationStateType",
    "QualityType",
    "RawValueTypeType",
    "RegionName",
    "ResolveToResourceTypeType",
    "ResourceServiceName",
    "ResourceTypeType",
    "ScalarTypeType",
    "ServiceName",
    "StorageTypeType",
    "TargetResourceTypeType",
    "TimeOrderingType",
    "TraversalDirectionType",
    "TraversalTypeType",
    "WaiterName",
    "WarmTierStateType",
)


AggregateTypeType = Literal["AVERAGE", "COUNT", "MAXIMUM", "MINIMUM", "STANDARD_DEVIATION", "SUM"]
AssetActiveWaiterName = Literal["asset_active"]
AssetErrorCodeType = Literal["INTERNAL_FAILURE"]
AssetModelActiveWaiterName = Literal["asset_model_active"]
AssetModelNotExistsWaiterName = Literal["asset_model_not_exists"]
AssetModelStateType = Literal["ACTIVE", "CREATING", "DELETING", "FAILED", "PROPAGATING", "UPDATING"]
AssetModelTypeType = Literal["ASSET_MODEL", "COMPONENT_MODEL", "INTERFACE"]
AssetModelVersionTypeType = Literal["ACTIVE", "LATEST"]
AssetNotExistsWaiterName = Literal["asset_not_exists"]
AssetRelationshipTypeType = Literal["HIERARCHY"]
AssetStateType = Literal["ACTIVE", "CREATING", "DELETING", "FAILED", "UPDATING"]
AuthModeType = Literal["IAM", "SSO"]
BatchEntryCompletionStatusType = Literal["ERROR", "SUCCESS"]
BatchGetAssetPropertyAggregatesErrorCodeType = Literal[
    "AccessDeniedException", "InvalidRequestException", "ResourceNotFoundException"
]
BatchGetAssetPropertyValueErrorCodeType = Literal[
    "AccessDeniedException", "InvalidRequestException", "ResourceNotFoundException"
]
BatchGetAssetPropertyValueHistoryErrorCodeType = Literal[
    "AccessDeniedException", "InvalidRequestException", "ResourceNotFoundException"
]
BatchPutAssetPropertyValueErrorCodeType = Literal[
    "AccessDeniedException",
    "ConflictingOperationException",
    "InternalFailureException",
    "InvalidRequestException",
    "LimitExceededException",
    "ResourceNotFoundException",
    "ServiceUnavailableException",
    "ThrottlingException",
    "TimestampOutOfRangeException",
]
CapabilitySyncStatusType = Literal[
    "IN_SYNC", "NOT_APPLICABLE", "OUT_OF_SYNC", "SYNC_FAILED", "UNKNOWN"
]
ColumnNameType = Literal[
    "ALIAS",
    "ASSET_ID",
    "DATA_TYPE",
    "PROPERTY_ID",
    "QUALITY",
    "TIMESTAMP_NANO_OFFSET",
    "TIMESTAMP_SECONDS",
    "VALUE",
]
ComputationModelStateType = Literal["ACTIVE", "CREATING", "DELETING", "FAILED", "UPDATING"]
ComputationModelTypeType = Literal["ANOMALY_DETECTION"]
ComputeLocationType = Literal["CLOUD", "EDGE"]
ConfigurationStateType = Literal["ACTIVE", "UPDATE_FAILED", "UPDATE_IN_PROGRESS"]
CoreDeviceOperatingSystemType = Literal["LINUX_AARCH64", "LINUX_AMD64", "WINDOWS_AMD64"]
DatasetSourceFormatType = Literal["KNOWLEDGE_BASE"]
DatasetSourceTypeType = Literal["KENDRA"]
DatasetStateType = Literal["ACTIVE", "CREATING", "DELETING", "FAILED", "UPDATING"]
DetailedErrorCodeType = Literal[
    "INCOMPATIBLE_COMPUTE_LOCATION", "INCOMPATIBLE_FORWARDING_CONFIGURATION"
]
DisassociatedDataStorageStateType = Literal["DISABLED", "ENABLED"]
EncryptionTypeType = Literal["KMS_BASED_ENCRYPTION", "SITEWISE_DEFAULT_ENCRYPTION"]
ErrorCodeType = Literal["INTERNAL_FAILURE", "VALIDATION_ERROR"]
ExecuteQueryPaginatorName = Literal["execute_query"]
ExecutionStateType = Literal["COMPLETED", "FAILED", "RUNNING"]
ForwardingConfigStateType = Literal["DISABLED", "ENABLED"]
GetAssetPropertyAggregatesPaginatorName = Literal["get_asset_property_aggregates"]
GetAssetPropertyValueHistoryPaginatorName = Literal["get_asset_property_value_history"]
GetInterpolatedAssetPropertyValuesPaginatorName = Literal["get_interpolated_asset_property_values"]
IdentityTypeType = Literal["GROUP", "IAM", "USER"]
ImageFileTypeType = Literal["PNG"]
JobStatusType = Literal[
    "CANCELLED", "COMPLETED", "COMPLETED_WITH_FAILURES", "FAILED", "PENDING", "RUNNING"
]
ListAccessPoliciesPaginatorName = Literal["list_access_policies"]
ListActionsPaginatorName = Literal["list_actions"]
ListAssetModelCompositeModelsPaginatorName = Literal["list_asset_model_composite_models"]
ListAssetModelPropertiesFilterType = Literal["ALL", "BASE"]
ListAssetModelPropertiesPaginatorName = Literal["list_asset_model_properties"]
ListAssetModelsPaginatorName = Literal["list_asset_models"]
ListAssetPropertiesFilterType = Literal["ALL", "BASE"]
ListAssetPropertiesPaginatorName = Literal["list_asset_properties"]
ListAssetRelationshipsPaginatorName = Literal["list_asset_relationships"]
ListAssetsFilterType = Literal["ALL", "TOP_LEVEL"]
ListAssetsPaginatorName = Literal["list_assets"]
ListAssociatedAssetsPaginatorName = Literal["list_associated_assets"]
ListBulkImportJobsFilterType = Literal[
    "ALL", "CANCELLED", "COMPLETED", "COMPLETED_WITH_FAILURES", "FAILED", "PENDING", "RUNNING"
]
ListBulkImportJobsPaginatorName = Literal["list_bulk_import_jobs"]
ListCompositionRelationshipsPaginatorName = Literal["list_composition_relationships"]
ListComputationModelDataBindingUsagesPaginatorName = Literal[
    "list_computation_model_data_binding_usages"
]
ListComputationModelResolveToResourcesPaginatorName = Literal[
    "list_computation_model_resolve_to_resources"
]
ListComputationModelsPaginatorName = Literal["list_computation_models"]
ListDashboardsPaginatorName = Literal["list_dashboards"]
ListDatasetsPaginatorName = Literal["list_datasets"]
ListExecutionsPaginatorName = Literal["list_executions"]
ListGatewaysPaginatorName = Literal["list_gateways"]
ListInterfaceRelationshipsPaginatorName = Literal["list_interface_relationships"]
ListPortalsPaginatorName = Literal["list_portals"]
ListProjectAssetsPaginatorName = Literal["list_project_assets"]
ListProjectsPaginatorName = Literal["list_projects"]
ListTimeSeriesPaginatorName = Literal["list_time_series"]
ListTimeSeriesTypeType = Literal["ASSOCIATED", "DISASSOCIATED"]
LoggingLevelType = Literal["ERROR", "INFO", "OFF"]
MonitorErrorCodeType = Literal["INTERNAL_FAILURE", "LIMIT_EXCEEDED", "VALIDATION_ERROR"]
PermissionType = Literal["ADMINISTRATOR", "VIEWER"]
PortalActiveWaiterName = Literal["portal_active"]
PortalNotExistsWaiterName = Literal["portal_not_exists"]
PortalStateType = Literal["ACTIVE", "CREATING", "DELETING", "FAILED", "PENDING", "UPDATING"]
PortalTypeType = Literal["SITEWISE_PORTAL_V1", "SITEWISE_PORTAL_V2"]
PropertyDataTypeType = Literal["BOOLEAN", "DOUBLE", "INTEGER", "STRING", "STRUCT"]
PropertyNotificationStateType = Literal["DISABLED", "ENABLED"]
QualityType = Literal["BAD", "GOOD", "UNCERTAIN"]
RawValueTypeType = Literal["B", "D", "I", "S", "U"]
ResolveToResourceTypeType = Literal["ASSET"]
ResourceTypeType = Literal["PORTAL", "PROJECT"]
ScalarTypeType = Literal["BOOLEAN", "DOUBLE", "INT", "STRING", "TIMESTAMP"]
StorageTypeType = Literal["MULTI_LAYER_STORAGE", "SITEWISE_DEFAULT_STORAGE"]
TargetResourceTypeType = Literal["ASSET", "COMPUTATION_MODEL"]
TimeOrderingType = Literal["ASCENDING", "DESCENDING"]
TraversalDirectionType = Literal["CHILD", "PARENT"]
TraversalTypeType = Literal["PATH_TO_ROOT"]
WarmTierStateType = Literal["DISABLED", "ENABLED"]
IoTSiteWiseServiceName = Literal["iotsitewise"]
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
    "execute_query",
    "get_asset_property_aggregates",
    "get_asset_property_value_history",
    "get_interpolated_asset_property_values",
    "list_access_policies",
    "list_actions",
    "list_asset_model_composite_models",
    "list_asset_model_properties",
    "list_asset_models",
    "list_asset_properties",
    "list_asset_relationships",
    "list_assets",
    "list_associated_assets",
    "list_bulk_import_jobs",
    "list_composition_relationships",
    "list_computation_model_data_binding_usages",
    "list_computation_model_resolve_to_resources",
    "list_computation_models",
    "list_dashboards",
    "list_datasets",
    "list_executions",
    "list_gateways",
    "list_interface_relationships",
    "list_portals",
    "list_project_assets",
    "list_projects",
    "list_time_series",
]
WaiterName = Literal[
    "asset_active",
    "asset_model_active",
    "asset_model_not_exists",
    "asset_not_exists",
    "portal_active",
    "portal_not_exists",
]
RegionName = Literal[
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ca-central-1",
    "eu-central-1",
    "eu-west-1",
    "us-east-1",
    "us-east-2",
    "us-west-2",
]
