"""
Type annotations for codeguru-security service type definitions.

[Documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeguru_security/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from mypy_boto3_codeguru_security.type_defs import FindingMetricsValuePerSeverityTypeDef

    data: FindingMetricsValuePerSeverityTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Union

from .literals import (
    AnalysisTypeType,
    ErrorCodeType,
    ScanStateType,
    ScanTypeType,
    SeverityType,
    StatusType,
)

if sys.version_info >= (3, 9):
    from builtins import dict as Dict
    from builtins import list as List
    from collections.abc import Mapping, Sequence
else:
    from typing import Dict, List, Mapping, Sequence
if sys.version_info >= (3, 12):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict

__all__ = (
    "AccountFindingsMetricTypeDef",
    "BatchGetFindingsErrorTypeDef",
    "BatchGetFindingsRequestTypeDef",
    "BatchGetFindingsResponseTypeDef",
    "CategoryWithFindingNumTypeDef",
    "CodeLineTypeDef",
    "CreateScanRequestTypeDef",
    "CreateScanResponseTypeDef",
    "CreateUploadUrlRequestTypeDef",
    "CreateUploadUrlResponseTypeDef",
    "EncryptionConfigTypeDef",
    "FilePathTypeDef",
    "FindingIdentifierTypeDef",
    "FindingMetricsValuePerSeverityTypeDef",
    "FindingTypeDef",
    "GetAccountConfigurationResponseTypeDef",
    "GetFindingsRequestPaginateTypeDef",
    "GetFindingsRequestTypeDef",
    "GetFindingsResponseTypeDef",
    "GetMetricsSummaryRequestTypeDef",
    "GetMetricsSummaryResponseTypeDef",
    "GetScanRequestTypeDef",
    "GetScanResponseTypeDef",
    "ListFindingsMetricsRequestPaginateTypeDef",
    "ListFindingsMetricsRequestTypeDef",
    "ListFindingsMetricsResponseTypeDef",
    "ListScansRequestPaginateTypeDef",
    "ListScansRequestTypeDef",
    "ListScansResponseTypeDef",
    "ListTagsForResourceRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "MetricsSummaryTypeDef",
    "PaginatorConfigTypeDef",
    "RecommendationTypeDef",
    "RemediationTypeDef",
    "ResourceIdTypeDef",
    "ResourceTypeDef",
    "ResponseMetadataTypeDef",
    "ScanNameWithFindingNumTypeDef",
    "ScanSummaryTypeDef",
    "SuggestedFixTypeDef",
    "TagResourceRequestTypeDef",
    "TimestampTypeDef",
    "UntagResourceRequestTypeDef",
    "UpdateAccountConfigurationRequestTypeDef",
    "UpdateAccountConfigurationResponseTypeDef",
    "VulnerabilityTypeDef",
)

class FindingMetricsValuePerSeverityTypeDef(TypedDict):
    info: NotRequired[float]
    low: NotRequired[float]
    medium: NotRequired[float]
    high: NotRequired[float]
    critical: NotRequired[float]

class BatchGetFindingsErrorTypeDef(TypedDict):
    scanName: str
    findingId: str
    errorCode: ErrorCodeType
    message: str

class FindingIdentifierTypeDef(TypedDict):
    scanName: str
    findingId: str

class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]

class CategoryWithFindingNumTypeDef(TypedDict):
    categoryName: NotRequired[str]
    findingNumber: NotRequired[int]

class CodeLineTypeDef(TypedDict):
    number: NotRequired[int]
    content: NotRequired[str]

class ResourceIdTypeDef(TypedDict):
    codeArtifactId: NotRequired[str]

class CreateUploadUrlRequestTypeDef(TypedDict):
    scanName: str

class EncryptionConfigTypeDef(TypedDict):
    kmsKeyArn: NotRequired[str]

ResourceTypeDef = TypedDict(
    "ResourceTypeDef",
    {
        "id": NotRequired[str],
        "subResourceId": NotRequired[str],
    },
)

class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]

class GetFindingsRequestTypeDef(TypedDict):
    scanName: str
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]
    status: NotRequired[StatusType]

TimestampTypeDef = Union[datetime, str]

class GetScanRequestTypeDef(TypedDict):
    scanName: str
    runId: NotRequired[str]

class ListScansRequestTypeDef(TypedDict):
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ScanSummaryTypeDef(TypedDict):
    scanState: ScanStateType
    createdAt: datetime
    scanName: str
    runId: str
    updatedAt: NotRequired[datetime]
    scanNameArn: NotRequired[str]

class ListTagsForResourceRequestTypeDef(TypedDict):
    resourceArn: str

class ScanNameWithFindingNumTypeDef(TypedDict):
    scanName: NotRequired[str]
    findingNumber: NotRequired[int]

class RecommendationTypeDef(TypedDict):
    text: NotRequired[str]
    url: NotRequired[str]

class SuggestedFixTypeDef(TypedDict):
    description: NotRequired[str]
    code: NotRequired[str]

class TagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tags: Mapping[str, str]

class UntagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tagKeys: Sequence[str]

class AccountFindingsMetricTypeDef(TypedDict):
    date: NotRequired[datetime]
    newFindings: NotRequired[FindingMetricsValuePerSeverityTypeDef]
    closedFindings: NotRequired[FindingMetricsValuePerSeverityTypeDef]
    openFindings: NotRequired[FindingMetricsValuePerSeverityTypeDef]
    meanTimeToClose: NotRequired[FindingMetricsValuePerSeverityTypeDef]

class BatchGetFindingsRequestTypeDef(TypedDict):
    findingIdentifiers: Sequence[FindingIdentifierTypeDef]

class CreateUploadUrlResponseTypeDef(TypedDict):
    s3Url: str
    requestHeaders: Dict[str, str]
    codeArtifactId: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetScanResponseTypeDef(TypedDict):
    scanName: str
    runId: str
    scanState: ScanStateType
    createdAt: datetime
    analysisType: AnalysisTypeType
    updatedAt: datetime
    numberOfRevisions: int
    scanNameArn: str
    errorMessage: str
    ResponseMetadata: ResponseMetadataTypeDef

class ListTagsForResourceResponseTypeDef(TypedDict):
    tags: Dict[str, str]
    ResponseMetadata: ResponseMetadataTypeDef

class FilePathTypeDef(TypedDict):
    name: NotRequired[str]
    path: NotRequired[str]
    startLine: NotRequired[int]
    endLine: NotRequired[int]
    codeSnippet: NotRequired[List[CodeLineTypeDef]]

class CreateScanRequestTypeDef(TypedDict):
    resourceId: ResourceIdTypeDef
    scanName: str
    clientToken: NotRequired[str]
    scanType: NotRequired[ScanTypeType]
    analysisType: NotRequired[AnalysisTypeType]
    tags: NotRequired[Mapping[str, str]]

class CreateScanResponseTypeDef(TypedDict):
    scanName: str
    runId: str
    resourceId: ResourceIdTypeDef
    scanState: ScanStateType
    scanNameArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetAccountConfigurationResponseTypeDef(TypedDict):
    encryptionConfig: EncryptionConfigTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class UpdateAccountConfigurationRequestTypeDef(TypedDict):
    encryptionConfig: EncryptionConfigTypeDef

class UpdateAccountConfigurationResponseTypeDef(TypedDict):
    encryptionConfig: EncryptionConfigTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GetFindingsRequestPaginateTypeDef(TypedDict):
    scanName: str
    status: NotRequired[StatusType]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListScansRequestPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class GetMetricsSummaryRequestTypeDef(TypedDict):
    date: TimestampTypeDef

class ListFindingsMetricsRequestPaginateTypeDef(TypedDict):
    startDate: TimestampTypeDef
    endDate: TimestampTypeDef
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListFindingsMetricsRequestTypeDef(TypedDict):
    startDate: TimestampTypeDef
    endDate: TimestampTypeDef
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ListScansResponseTypeDef(TypedDict):
    summaries: List[ScanSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class MetricsSummaryTypeDef(TypedDict):
    date: NotRequired[datetime]
    openFindings: NotRequired[FindingMetricsValuePerSeverityTypeDef]
    categoriesWithMostFindings: NotRequired[List[CategoryWithFindingNumTypeDef]]
    scansWithMostOpenFindings: NotRequired[List[ScanNameWithFindingNumTypeDef]]
    scansWithMostOpenCriticalFindings: NotRequired[List[ScanNameWithFindingNumTypeDef]]

class RemediationTypeDef(TypedDict):
    recommendation: NotRequired[RecommendationTypeDef]
    suggestedFixes: NotRequired[List[SuggestedFixTypeDef]]

class ListFindingsMetricsResponseTypeDef(TypedDict):
    findingsMetrics: List[AccountFindingsMetricTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

VulnerabilityTypeDef = TypedDict(
    "VulnerabilityTypeDef",
    {
        "referenceUrls": NotRequired[List[str]],
        "relatedVulnerabilities": NotRequired[List[str]],
        "id": NotRequired[str],
        "filePath": NotRequired[FilePathTypeDef],
        "itemCount": NotRequired[int],
    },
)

class GetMetricsSummaryResponseTypeDef(TypedDict):
    metricsSummary: MetricsSummaryTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

FindingTypeDef = TypedDict(
    "FindingTypeDef",
    {
        "createdAt": NotRequired[datetime],
        "description": NotRequired[str],
        "generatorId": NotRequired[str],
        "id": NotRequired[str],
        "updatedAt": NotRequired[datetime],
        "type": NotRequired[str],
        "status": NotRequired[StatusType],
        "resource": NotRequired[ResourceTypeDef],
        "vulnerability": NotRequired[VulnerabilityTypeDef],
        "severity": NotRequired[SeverityType],
        "remediation": NotRequired[RemediationTypeDef],
        "title": NotRequired[str],
        "detectorTags": NotRequired[List[str]],
        "detectorId": NotRequired[str],
        "detectorName": NotRequired[str],
        "ruleId": NotRequired[str],
    },
)

class BatchGetFindingsResponseTypeDef(TypedDict):
    findings: List[FindingTypeDef]
    failedFindings: List[BatchGetFindingsErrorTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class GetFindingsResponseTypeDef(TypedDict):
    findings: List[FindingTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]
