"""
Type annotations for bedrock-runtime service type definitions.

[Documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_runtime/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from mypy_boto3_bedrock_runtime.type_defs import GuardrailOutputContentTypeDef

    data: GuardrailOutputContentTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import IO, Any, Union

from botocore.eventstream import EventStream
from botocore.response import StreamingBody

from .literals import (
    AsyncInvokeStatusType,
    ConversationRoleType,
    DocumentFormatType,
    GuardrailActionType,
    GuardrailAutomatedReasoningLogicWarningTypeType,
    GuardrailContentFilterConfidenceType,
    GuardrailContentFilterStrengthType,
    GuardrailContentFilterTypeType,
    GuardrailContentPolicyActionType,
    GuardrailContentQualifierType,
    GuardrailContentSourceType,
    GuardrailContextualGroundingFilterTypeType,
    GuardrailContextualGroundingPolicyActionType,
    GuardrailConverseContentQualifierType,
    GuardrailConverseImageFormatType,
    GuardrailImageFormatType,
    GuardrailOutputScopeType,
    GuardrailPiiEntityTypeType,
    GuardrailSensitiveInformationPolicyActionType,
    GuardrailStreamProcessingModeType,
    GuardrailTopicPolicyActionType,
    GuardrailTraceType,
    GuardrailWordPolicyActionType,
    ImageFormatType,
    PerformanceConfigLatencyType,
    SortOrderType,
    StopReasonType,
    ToolResultStatusType,
    TraceType,
    VideoFormatType,
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
    "ApplyGuardrailRequestTypeDef",
    "ApplyGuardrailResponseTypeDef",
    "AsyncInvokeOutputDataConfigTypeDef",
    "AsyncInvokeS3OutputDataConfigTypeDef",
    "AsyncInvokeSummaryTypeDef",
    "BidirectionalInputPayloadPartTypeDef",
    "BidirectionalOutputPayloadPartTypeDef",
    "BlobTypeDef",
    "CachePointBlockTypeDef",
    "CitationGeneratedContentTypeDef",
    "CitationLocationTypeDef",
    "CitationOutputTypeDef",
    "CitationSourceContentDeltaTypeDef",
    "CitationSourceContentTypeDef",
    "CitationTypeDef",
    "CitationUnionTypeDef",
    "CitationsConfigTypeDef",
    "CitationsContentBlockOutputTypeDef",
    "CitationsContentBlockTypeDef",
    "CitationsContentBlockUnionTypeDef",
    "CitationsDeltaTypeDef",
    "ContentBlockDeltaEventTypeDef",
    "ContentBlockDeltaTypeDef",
    "ContentBlockOutputTypeDef",
    "ContentBlockStartEventTypeDef",
    "ContentBlockStartTypeDef",
    "ContentBlockStopEventTypeDef",
    "ContentBlockTypeDef",
    "ContentBlockUnionTypeDef",
    "ConverseMetricsTypeDef",
    "ConverseOutputTypeDef",
    "ConverseRequestTypeDef",
    "ConverseResponseTypeDef",
    "ConverseStreamMetadataEventTypeDef",
    "ConverseStreamMetricsTypeDef",
    "ConverseStreamOutputTypeDef",
    "ConverseStreamRequestTypeDef",
    "ConverseStreamResponseTypeDef",
    "ConverseStreamTraceTypeDef",
    "ConverseTokensRequestTypeDef",
    "ConverseTraceTypeDef",
    "CountTokensInputTypeDef",
    "CountTokensRequestTypeDef",
    "CountTokensResponseTypeDef",
    "DocumentBlockOutputTypeDef",
    "DocumentBlockTypeDef",
    "DocumentBlockUnionTypeDef",
    "DocumentCharLocationTypeDef",
    "DocumentChunkLocationTypeDef",
    "DocumentContentBlockTypeDef",
    "DocumentPageLocationTypeDef",
    "DocumentSourceOutputTypeDef",
    "DocumentSourceTypeDef",
    "DocumentSourceUnionTypeDef",
    "GetAsyncInvokeRequestTypeDef",
    "GetAsyncInvokeResponseTypeDef",
    "GuardrailAssessmentTypeDef",
    "GuardrailAutomatedReasoningFindingTypeDef",
    "GuardrailAutomatedReasoningImpossibleFindingTypeDef",
    "GuardrailAutomatedReasoningInputTextReferenceTypeDef",
    "GuardrailAutomatedReasoningInvalidFindingTypeDef",
    "GuardrailAutomatedReasoningLogicWarningTypeDef",
    "GuardrailAutomatedReasoningPolicyAssessmentTypeDef",
    "GuardrailAutomatedReasoningRuleTypeDef",
    "GuardrailAutomatedReasoningSatisfiableFindingTypeDef",
    "GuardrailAutomatedReasoningScenarioTypeDef",
    "GuardrailAutomatedReasoningStatementTypeDef",
    "GuardrailAutomatedReasoningTranslationAmbiguousFindingTypeDef",
    "GuardrailAutomatedReasoningTranslationOptionTypeDef",
    "GuardrailAutomatedReasoningTranslationTypeDef",
    "GuardrailAutomatedReasoningValidFindingTypeDef",
    "GuardrailConfigurationTypeDef",
    "GuardrailContentBlockTypeDef",
    "GuardrailContentFilterTypeDef",
    "GuardrailContentPolicyAssessmentTypeDef",
    "GuardrailContextualGroundingFilterTypeDef",
    "GuardrailContextualGroundingPolicyAssessmentTypeDef",
    "GuardrailConverseContentBlockOutputTypeDef",
    "GuardrailConverseContentBlockTypeDef",
    "GuardrailConverseContentBlockUnionTypeDef",
    "GuardrailConverseImageBlockOutputTypeDef",
    "GuardrailConverseImageBlockTypeDef",
    "GuardrailConverseImageBlockUnionTypeDef",
    "GuardrailConverseImageSourceOutputTypeDef",
    "GuardrailConverseImageSourceTypeDef",
    "GuardrailConverseImageSourceUnionTypeDef",
    "GuardrailConverseTextBlockOutputTypeDef",
    "GuardrailConverseTextBlockTypeDef",
    "GuardrailConverseTextBlockUnionTypeDef",
    "GuardrailCoverageTypeDef",
    "GuardrailCustomWordTypeDef",
    "GuardrailImageBlockTypeDef",
    "GuardrailImageCoverageTypeDef",
    "GuardrailImageSourceTypeDef",
    "GuardrailInvocationMetricsTypeDef",
    "GuardrailManagedWordTypeDef",
    "GuardrailOutputContentTypeDef",
    "GuardrailPiiEntityFilterTypeDef",
    "GuardrailRegexFilterTypeDef",
    "GuardrailSensitiveInformationPolicyAssessmentTypeDef",
    "GuardrailStreamConfigurationTypeDef",
    "GuardrailTextBlockTypeDef",
    "GuardrailTextCharactersCoverageTypeDef",
    "GuardrailTopicPolicyAssessmentTypeDef",
    "GuardrailTopicTypeDef",
    "GuardrailTraceAssessmentTypeDef",
    "GuardrailUsageTypeDef",
    "GuardrailWordPolicyAssessmentTypeDef",
    "ImageBlockOutputTypeDef",
    "ImageBlockTypeDef",
    "ImageBlockUnionTypeDef",
    "ImageSourceOutputTypeDef",
    "ImageSourceTypeDef",
    "ImageSourceUnionTypeDef",
    "InferenceConfigurationTypeDef",
    "InternalServerExceptionTypeDef",
    "InvokeModelRequestTypeDef",
    "InvokeModelResponseTypeDef",
    "InvokeModelTokensRequestTypeDef",
    "InvokeModelWithBidirectionalStreamInputTypeDef",
    "InvokeModelWithBidirectionalStreamOutputTypeDef",
    "InvokeModelWithBidirectionalStreamRequestTypeDef",
    "InvokeModelWithBidirectionalStreamResponseTypeDef",
    "InvokeModelWithResponseStreamRequestTypeDef",
    "InvokeModelWithResponseStreamResponseTypeDef",
    "ListAsyncInvokesRequestPaginateTypeDef",
    "ListAsyncInvokesRequestTypeDef",
    "ListAsyncInvokesResponseTypeDef",
    "MessageOutputTypeDef",
    "MessageStartEventTypeDef",
    "MessageStopEventTypeDef",
    "MessageTypeDef",
    "MessageUnionTypeDef",
    "ModelStreamErrorExceptionTypeDef",
    "ModelTimeoutExceptionTypeDef",
    "PaginatorConfigTypeDef",
    "PayloadPartTypeDef",
    "PerformanceConfigurationTypeDef",
    "PromptRouterTraceTypeDef",
    "PromptVariableValuesTypeDef",
    "ReasoningContentBlockDeltaTypeDef",
    "ReasoningContentBlockOutputTypeDef",
    "ReasoningContentBlockTypeDef",
    "ReasoningContentBlockUnionTypeDef",
    "ReasoningTextBlockTypeDef",
    "ResponseMetadataTypeDef",
    "ResponseStreamTypeDef",
    "S3LocationTypeDef",
    "ServiceUnavailableExceptionTypeDef",
    "SpecificToolChoiceTypeDef",
    "StartAsyncInvokeRequestTypeDef",
    "StartAsyncInvokeResponseTypeDef",
    "SystemContentBlockTypeDef",
    "TagTypeDef",
    "ThrottlingExceptionTypeDef",
    "TimestampTypeDef",
    "TokenUsageTypeDef",
    "ToolChoiceTypeDef",
    "ToolConfigurationTypeDef",
    "ToolInputSchemaTypeDef",
    "ToolResultBlockOutputTypeDef",
    "ToolResultBlockTypeDef",
    "ToolResultBlockUnionTypeDef",
    "ToolResultContentBlockOutputTypeDef",
    "ToolResultContentBlockTypeDef",
    "ToolResultContentBlockUnionTypeDef",
    "ToolSpecificationTypeDef",
    "ToolTypeDef",
    "ToolUseBlockDeltaTypeDef",
    "ToolUseBlockOutputTypeDef",
    "ToolUseBlockStartTypeDef",
    "ToolUseBlockTypeDef",
    "ToolUseBlockUnionTypeDef",
    "ValidationExceptionTypeDef",
    "VideoBlockOutputTypeDef",
    "VideoBlockTypeDef",
    "VideoBlockUnionTypeDef",
    "VideoSourceOutputTypeDef",
    "VideoSourceTypeDef",
    "VideoSourceUnionTypeDef",
)

class GuardrailOutputContentTypeDef(TypedDict):
    text: NotRequired[str]

class GuardrailUsageTypeDef(TypedDict):
    topicPolicyUnits: int
    contentPolicyUnits: int
    wordPolicyUnits: int
    sensitiveInformationPolicyUnits: int
    sensitiveInformationPolicyFreeUnits: int
    contextualGroundingPolicyUnits: int
    contentPolicyImageUnits: NotRequired[int]
    automatedReasoningPolicyUnits: NotRequired[int]
    automatedReasoningPolicies: NotRequired[int]

class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]

class AsyncInvokeS3OutputDataConfigTypeDef(TypedDict):
    s3Uri: str
    kmsKeyId: NotRequired[str]
    bucketOwner: NotRequired[str]

BlobTypeDef = Union[str, bytes, IO[Any], StreamingBody]
BidirectionalOutputPayloadPartTypeDef = TypedDict(
    "BidirectionalOutputPayloadPartTypeDef",
    {
        "bytes": NotRequired[bytes],
    },
)
CachePointBlockTypeDef = TypedDict(
    "CachePointBlockTypeDef",
    {
        "type": Literal["default"],
    },
)

class CitationGeneratedContentTypeDef(TypedDict):
    text: NotRequired[str]

class DocumentCharLocationTypeDef(TypedDict):
    documentIndex: NotRequired[int]
    start: NotRequired[int]
    end: NotRequired[int]

class DocumentChunkLocationTypeDef(TypedDict):
    documentIndex: NotRequired[int]
    start: NotRequired[int]
    end: NotRequired[int]

class DocumentPageLocationTypeDef(TypedDict):
    documentIndex: NotRequired[int]
    start: NotRequired[int]
    end: NotRequired[int]

class CitationSourceContentTypeDef(TypedDict):
    text: NotRequired[str]

class CitationSourceContentDeltaTypeDef(TypedDict):
    text: NotRequired[str]

class CitationsConfigTypeDef(TypedDict):
    enabled: bool

class ReasoningContentBlockDeltaTypeDef(TypedDict):
    text: NotRequired[str]
    redactedContent: NotRequired[bytes]
    signature: NotRequired[str]

ToolUseBlockDeltaTypeDef = TypedDict(
    "ToolUseBlockDeltaTypeDef",
    {
        "input": str,
    },
)
ToolUseBlockOutputTypeDef = TypedDict(
    "ToolUseBlockOutputTypeDef",
    {
        "toolUseId": str,
        "name": str,
        "input": Dict[str, Any],
    },
)

class ToolUseBlockStartTypeDef(TypedDict):
    toolUseId: str
    name: str

class ContentBlockStopEventTypeDef(TypedDict):
    contentBlockIndex: int

class ConverseMetricsTypeDef(TypedDict):
    latencyMs: int

class GuardrailConfigurationTypeDef(TypedDict):
    guardrailIdentifier: str
    guardrailVersion: str
    trace: NotRequired[GuardrailTraceType]

class InferenceConfigurationTypeDef(TypedDict):
    maxTokens: NotRequired[int]
    temperature: NotRequired[float]
    topP: NotRequired[float]
    stopSequences: NotRequired[Sequence[str]]

class PerformanceConfigurationTypeDef(TypedDict):
    latency: NotRequired[PerformanceConfigLatencyType]

class PromptVariableValuesTypeDef(TypedDict):
    text: NotRequired[str]

class TokenUsageTypeDef(TypedDict):
    inputTokens: int
    outputTokens: int
    totalTokens: int
    cacheReadInputTokens: NotRequired[int]
    cacheWriteInputTokens: NotRequired[int]

class ConverseStreamMetricsTypeDef(TypedDict):
    latencyMs: int

class InternalServerExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class MessageStartEventTypeDef(TypedDict):
    role: ConversationRoleType

class MessageStopEventTypeDef(TypedDict):
    stopReason: StopReasonType
    additionalModelResponseFields: NotRequired[Dict[str, Any]]

class ModelStreamErrorExceptionTypeDef(TypedDict):
    message: NotRequired[str]
    originalStatusCode: NotRequired[int]
    originalMessage: NotRequired[str]

class ServiceUnavailableExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ThrottlingExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ValidationExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class GuardrailStreamConfigurationTypeDef(TypedDict):
    guardrailIdentifier: str
    guardrailVersion: str
    trace: NotRequired[GuardrailTraceType]
    streamProcessingMode: NotRequired[GuardrailStreamProcessingModeType]

class PromptRouterTraceTypeDef(TypedDict):
    invokedModelId: NotRequired[str]

class DocumentContentBlockTypeDef(TypedDict):
    text: NotRequired[str]

class S3LocationTypeDef(TypedDict):
    uri: str
    bucketOwner: NotRequired[str]

class GetAsyncInvokeRequestTypeDef(TypedDict):
    invocationArn: str

class GuardrailAutomatedReasoningRuleTypeDef(TypedDict):
    identifier: NotRequired[str]
    policyVersionArn: NotRequired[str]

class GuardrailAutomatedReasoningInputTextReferenceTypeDef(TypedDict):
    text: NotRequired[str]

class GuardrailAutomatedReasoningStatementTypeDef(TypedDict):
    logic: NotRequired[str]
    naturalLanguage: NotRequired[str]

class GuardrailTextBlockTypeDef(TypedDict):
    text: str
    qualifiers: NotRequired[Sequence[GuardrailContentQualifierType]]

GuardrailContentFilterTypeDef = TypedDict(
    "GuardrailContentFilterTypeDef",
    {
        "type": GuardrailContentFilterTypeType,
        "confidence": GuardrailContentFilterConfidenceType,
        "action": GuardrailContentPolicyActionType,
        "filterStrength": NotRequired[GuardrailContentFilterStrengthType],
        "detected": NotRequired[bool],
    },
)
GuardrailContextualGroundingFilterTypeDef = TypedDict(
    "GuardrailContextualGroundingFilterTypeDef",
    {
        "type": GuardrailContextualGroundingFilterTypeType,
        "threshold": float,
        "score": float,
        "action": GuardrailContextualGroundingPolicyActionType,
        "detected": NotRequired[bool],
    },
)

class GuardrailConverseTextBlockOutputTypeDef(TypedDict):
    text: str
    qualifiers: NotRequired[List[GuardrailConverseContentQualifierType]]

GuardrailConverseImageSourceOutputTypeDef = TypedDict(
    "GuardrailConverseImageSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
    },
)

class GuardrailConverseTextBlockTypeDef(TypedDict):
    text: str
    qualifiers: NotRequired[Sequence[GuardrailConverseContentQualifierType]]

class GuardrailImageCoverageTypeDef(TypedDict):
    guarded: NotRequired[int]
    total: NotRequired[int]

class GuardrailTextCharactersCoverageTypeDef(TypedDict):
    guarded: NotRequired[int]
    total: NotRequired[int]

class GuardrailCustomWordTypeDef(TypedDict):
    match: str
    action: GuardrailWordPolicyActionType
    detected: NotRequired[bool]

GuardrailManagedWordTypeDef = TypedDict(
    "GuardrailManagedWordTypeDef",
    {
        "match": str,
        "type": Literal["PROFANITY"],
        "action": GuardrailWordPolicyActionType,
        "detected": NotRequired[bool],
    },
)
GuardrailPiiEntityFilterTypeDef = TypedDict(
    "GuardrailPiiEntityFilterTypeDef",
    {
        "match": str,
        "type": GuardrailPiiEntityTypeType,
        "action": GuardrailSensitiveInformationPolicyActionType,
        "detected": NotRequired[bool],
    },
)

class GuardrailRegexFilterTypeDef(TypedDict):
    action: GuardrailSensitiveInformationPolicyActionType
    name: NotRequired[str]
    match: NotRequired[str]
    regex: NotRequired[str]
    detected: NotRequired[bool]

GuardrailTopicTypeDef = TypedDict(
    "GuardrailTopicTypeDef",
    {
        "name": str,
        "type": Literal["DENY"],
        "action": GuardrailTopicPolicyActionType,
        "detected": NotRequired[bool],
    },
)

class ModelTimeoutExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]

TimestampTypeDef = Union[datetime, str]
PayloadPartTypeDef = TypedDict(
    "PayloadPartTypeDef",
    {
        "bytes": NotRequired[bytes],
    },
)

class ReasoningTextBlockTypeDef(TypedDict):
    text: str
    signature: NotRequired[str]

class SpecificToolChoiceTypeDef(TypedDict):
    name: str

class TagTypeDef(TypedDict):
    key: str
    value: str

class ToolInputSchemaTypeDef(TypedDict):
    json: NotRequired[Mapping[str, Any]]

ToolUseBlockTypeDef = TypedDict(
    "ToolUseBlockTypeDef",
    {
        "toolUseId": str,
        "name": str,
        "input": Mapping[str, Any],
    },
)

class CountTokensResponseTypeDef(TypedDict):
    inputTokens: int
    ResponseMetadata: ResponseMetadataTypeDef

class InvokeModelResponseTypeDef(TypedDict):
    body: StreamingBody
    contentType: str
    performanceConfigLatency: PerformanceConfigLatencyType
    ResponseMetadata: ResponseMetadataTypeDef

class StartAsyncInvokeResponseTypeDef(TypedDict):
    invocationArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class AsyncInvokeOutputDataConfigTypeDef(TypedDict):
    s3OutputDataConfig: NotRequired[AsyncInvokeS3OutputDataConfigTypeDef]

BidirectionalInputPayloadPartTypeDef = TypedDict(
    "BidirectionalInputPayloadPartTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
    },
)
GuardrailConverseImageSourceTypeDef = TypedDict(
    "GuardrailConverseImageSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
    },
)
GuardrailImageSourceTypeDef = TypedDict(
    "GuardrailImageSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
    },
)

class InvokeModelRequestTypeDef(TypedDict):
    modelId: str
    body: NotRequired[BlobTypeDef]
    contentType: NotRequired[str]
    accept: NotRequired[str]
    trace: NotRequired[TraceType]
    guardrailIdentifier: NotRequired[str]
    guardrailVersion: NotRequired[str]
    performanceConfigLatency: NotRequired[PerformanceConfigLatencyType]

class InvokeModelTokensRequestTypeDef(TypedDict):
    body: BlobTypeDef

class InvokeModelWithResponseStreamRequestTypeDef(TypedDict):
    modelId: str
    body: NotRequired[BlobTypeDef]
    contentType: NotRequired[str]
    accept: NotRequired[str]
    trace: NotRequired[TraceType]
    guardrailIdentifier: NotRequired[str]
    guardrailVersion: NotRequired[str]
    performanceConfigLatency: NotRequired[PerformanceConfigLatencyType]

class CitationLocationTypeDef(TypedDict):
    documentChar: NotRequired[DocumentCharLocationTypeDef]
    documentPage: NotRequired[DocumentPageLocationTypeDef]
    documentChunk: NotRequired[DocumentChunkLocationTypeDef]

class ContentBlockStartTypeDef(TypedDict):
    toolUse: NotRequired[ToolUseBlockStartTypeDef]

DocumentSourceOutputTypeDef = TypedDict(
    "DocumentSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
        "s3Location": NotRequired[S3LocationTypeDef],
        "text": NotRequired[str],
        "content": NotRequired[List[DocumentContentBlockTypeDef]],
    },
)
DocumentSourceTypeDef = TypedDict(
    "DocumentSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
        "s3Location": NotRequired[S3LocationTypeDef],
        "text": NotRequired[str],
        "content": NotRequired[Sequence[DocumentContentBlockTypeDef]],
    },
)
ImageSourceOutputTypeDef = TypedDict(
    "ImageSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)
ImageSourceTypeDef = TypedDict(
    "ImageSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)
VideoSourceOutputTypeDef = TypedDict(
    "VideoSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)
VideoSourceTypeDef = TypedDict(
    "VideoSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)
GuardrailAutomatedReasoningLogicWarningTypeDef = TypedDict(
    "GuardrailAutomatedReasoningLogicWarningTypeDef",
    {
        "type": NotRequired[GuardrailAutomatedReasoningLogicWarningTypeType],
        "premises": NotRequired[List[GuardrailAutomatedReasoningStatementTypeDef]],
        "claims": NotRequired[List[GuardrailAutomatedReasoningStatementTypeDef]],
    },
)

class GuardrailAutomatedReasoningScenarioTypeDef(TypedDict):
    statements: NotRequired[List[GuardrailAutomatedReasoningStatementTypeDef]]

class GuardrailAutomatedReasoningTranslationTypeDef(TypedDict):
    premises: NotRequired[List[GuardrailAutomatedReasoningStatementTypeDef]]
    claims: NotRequired[List[GuardrailAutomatedReasoningStatementTypeDef]]
    untranslatedPremises: NotRequired[List[GuardrailAutomatedReasoningInputTextReferenceTypeDef]]
    untranslatedClaims: NotRequired[List[GuardrailAutomatedReasoningInputTextReferenceTypeDef]]
    confidence: NotRequired[float]

class GuardrailContentPolicyAssessmentTypeDef(TypedDict):
    filters: List[GuardrailContentFilterTypeDef]

class GuardrailContextualGroundingPolicyAssessmentTypeDef(TypedDict):
    filters: NotRequired[List[GuardrailContextualGroundingFilterTypeDef]]

GuardrailConverseImageBlockOutputTypeDef = TypedDict(
    "GuardrailConverseImageBlockOutputTypeDef",
    {
        "format": GuardrailConverseImageFormatType,
        "source": GuardrailConverseImageSourceOutputTypeDef,
    },
)
GuardrailConverseTextBlockUnionTypeDef = Union[
    GuardrailConverseTextBlockTypeDef, GuardrailConverseTextBlockOutputTypeDef
]

class GuardrailCoverageTypeDef(TypedDict):
    textCharacters: NotRequired[GuardrailTextCharactersCoverageTypeDef]
    images: NotRequired[GuardrailImageCoverageTypeDef]

class GuardrailWordPolicyAssessmentTypeDef(TypedDict):
    customWords: List[GuardrailCustomWordTypeDef]
    managedWordLists: List[GuardrailManagedWordTypeDef]

class GuardrailSensitiveInformationPolicyAssessmentTypeDef(TypedDict):
    piiEntities: List[GuardrailPiiEntityFilterTypeDef]
    regexes: List[GuardrailRegexFilterTypeDef]

class GuardrailTopicPolicyAssessmentTypeDef(TypedDict):
    topics: List[GuardrailTopicTypeDef]

class InvokeModelWithBidirectionalStreamOutputTypeDef(TypedDict):
    chunk: NotRequired[BidirectionalOutputPayloadPartTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    modelStreamErrorException: NotRequired[ModelStreamErrorExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    modelTimeoutException: NotRequired[ModelTimeoutExceptionTypeDef]
    serviceUnavailableException: NotRequired[ServiceUnavailableExceptionTypeDef]

class ListAsyncInvokesRequestPaginateTypeDef(TypedDict):
    submitTimeAfter: NotRequired[TimestampTypeDef]
    submitTimeBefore: NotRequired[TimestampTypeDef]
    statusEquals: NotRequired[AsyncInvokeStatusType]
    sortBy: NotRequired[Literal["SubmissionTime"]]
    sortOrder: NotRequired[SortOrderType]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListAsyncInvokesRequestTypeDef(TypedDict):
    submitTimeAfter: NotRequired[TimestampTypeDef]
    submitTimeBefore: NotRequired[TimestampTypeDef]
    statusEquals: NotRequired[AsyncInvokeStatusType]
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]
    sortBy: NotRequired[Literal["SubmissionTime"]]
    sortOrder: NotRequired[SortOrderType]

class ResponseStreamTypeDef(TypedDict):
    chunk: NotRequired[PayloadPartTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    modelStreamErrorException: NotRequired[ModelStreamErrorExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    modelTimeoutException: NotRequired[ModelTimeoutExceptionTypeDef]
    serviceUnavailableException: NotRequired[ServiceUnavailableExceptionTypeDef]

class ReasoningContentBlockOutputTypeDef(TypedDict):
    reasoningText: NotRequired[ReasoningTextBlockTypeDef]
    redactedContent: NotRequired[bytes]

class ReasoningContentBlockTypeDef(TypedDict):
    reasoningText: NotRequired[ReasoningTextBlockTypeDef]
    redactedContent: NotRequired[BlobTypeDef]

ToolChoiceTypeDef = TypedDict(
    "ToolChoiceTypeDef",
    {
        "auto": NotRequired[Mapping[str, Any]],
        "any": NotRequired[Mapping[str, Any]],
        "tool": NotRequired[SpecificToolChoiceTypeDef],
    },
)

class ToolSpecificationTypeDef(TypedDict):
    name: str
    inputSchema: ToolInputSchemaTypeDef
    description: NotRequired[str]

ToolUseBlockUnionTypeDef = Union[ToolUseBlockTypeDef, ToolUseBlockOutputTypeDef]

class AsyncInvokeSummaryTypeDef(TypedDict):
    invocationArn: str
    modelArn: str
    submitTime: datetime
    outputDataConfig: AsyncInvokeOutputDataConfigTypeDef
    clientRequestToken: NotRequired[str]
    status: NotRequired[AsyncInvokeStatusType]
    failureMessage: NotRequired[str]
    lastModifiedTime: NotRequired[datetime]
    endTime: NotRequired[datetime]

class GetAsyncInvokeResponseTypeDef(TypedDict):
    invocationArn: str
    modelArn: str
    clientRequestToken: str
    status: AsyncInvokeStatusType
    failureMessage: str
    submitTime: datetime
    lastModifiedTime: datetime
    endTime: datetime
    outputDataConfig: AsyncInvokeOutputDataConfigTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class StartAsyncInvokeRequestTypeDef(TypedDict):
    modelId: str
    modelInput: Mapping[str, Any]
    outputDataConfig: AsyncInvokeOutputDataConfigTypeDef
    clientRequestToken: NotRequired[str]
    tags: NotRequired[Sequence[TagTypeDef]]

class InvokeModelWithBidirectionalStreamInputTypeDef(TypedDict):
    chunk: NotRequired[BidirectionalInputPayloadPartTypeDef]

GuardrailConverseImageSourceUnionTypeDef = Union[
    GuardrailConverseImageSourceTypeDef, GuardrailConverseImageSourceOutputTypeDef
]
GuardrailImageBlockTypeDef = TypedDict(
    "GuardrailImageBlockTypeDef",
    {
        "format": GuardrailImageFormatType,
        "source": GuardrailImageSourceTypeDef,
    },
)

class CitationOutputTypeDef(TypedDict):
    title: NotRequired[str]
    sourceContent: NotRequired[List[CitationSourceContentTypeDef]]
    location: NotRequired[CitationLocationTypeDef]

class CitationTypeDef(TypedDict):
    title: NotRequired[str]
    sourceContent: NotRequired[Sequence[CitationSourceContentTypeDef]]
    location: NotRequired[CitationLocationTypeDef]

class CitationsDeltaTypeDef(TypedDict):
    title: NotRequired[str]
    sourceContent: NotRequired[List[CitationSourceContentDeltaTypeDef]]
    location: NotRequired[CitationLocationTypeDef]

class ContentBlockStartEventTypeDef(TypedDict):
    start: ContentBlockStartTypeDef
    contentBlockIndex: int

DocumentBlockOutputTypeDef = TypedDict(
    "DocumentBlockOutputTypeDef",
    {
        "name": str,
        "source": DocumentSourceOutputTypeDef,
        "format": NotRequired[DocumentFormatType],
        "context": NotRequired[str],
        "citations": NotRequired[CitationsConfigTypeDef],
    },
)
DocumentSourceUnionTypeDef = Union[DocumentSourceTypeDef, DocumentSourceOutputTypeDef]
ImageBlockOutputTypeDef = TypedDict(
    "ImageBlockOutputTypeDef",
    {
        "format": ImageFormatType,
        "source": ImageSourceOutputTypeDef,
    },
)
ImageSourceUnionTypeDef = Union[ImageSourceTypeDef, ImageSourceOutputTypeDef]
VideoBlockOutputTypeDef = TypedDict(
    "VideoBlockOutputTypeDef",
    {
        "format": VideoFormatType,
        "source": VideoSourceOutputTypeDef,
    },
)
VideoSourceUnionTypeDef = Union[VideoSourceTypeDef, VideoSourceOutputTypeDef]

class GuardrailAutomatedReasoningImpossibleFindingTypeDef(TypedDict):
    translation: NotRequired[GuardrailAutomatedReasoningTranslationTypeDef]
    contradictingRules: NotRequired[List[GuardrailAutomatedReasoningRuleTypeDef]]
    logicWarning: NotRequired[GuardrailAutomatedReasoningLogicWarningTypeDef]

class GuardrailAutomatedReasoningInvalidFindingTypeDef(TypedDict):
    translation: NotRequired[GuardrailAutomatedReasoningTranslationTypeDef]
    contradictingRules: NotRequired[List[GuardrailAutomatedReasoningRuleTypeDef]]
    logicWarning: NotRequired[GuardrailAutomatedReasoningLogicWarningTypeDef]

class GuardrailAutomatedReasoningSatisfiableFindingTypeDef(TypedDict):
    translation: NotRequired[GuardrailAutomatedReasoningTranslationTypeDef]
    claimsTrueScenario: NotRequired[GuardrailAutomatedReasoningScenarioTypeDef]
    claimsFalseScenario: NotRequired[GuardrailAutomatedReasoningScenarioTypeDef]
    logicWarning: NotRequired[GuardrailAutomatedReasoningLogicWarningTypeDef]

class GuardrailAutomatedReasoningTranslationOptionTypeDef(TypedDict):
    translations: NotRequired[List[GuardrailAutomatedReasoningTranslationTypeDef]]

class GuardrailAutomatedReasoningValidFindingTypeDef(TypedDict):
    translation: NotRequired[GuardrailAutomatedReasoningTranslationTypeDef]
    claimsTrueScenario: NotRequired[GuardrailAutomatedReasoningScenarioTypeDef]
    supportingRules: NotRequired[List[GuardrailAutomatedReasoningRuleTypeDef]]
    logicWarning: NotRequired[GuardrailAutomatedReasoningLogicWarningTypeDef]

class GuardrailConverseContentBlockOutputTypeDef(TypedDict):
    text: NotRequired[GuardrailConverseTextBlockOutputTypeDef]
    image: NotRequired[GuardrailConverseImageBlockOutputTypeDef]

class GuardrailInvocationMetricsTypeDef(TypedDict):
    guardrailProcessingLatency: NotRequired[int]
    usage: NotRequired[GuardrailUsageTypeDef]
    guardrailCoverage: NotRequired[GuardrailCoverageTypeDef]

class InvokeModelWithBidirectionalStreamResponseTypeDef(TypedDict):
    body: EventStream[InvokeModelWithBidirectionalStreamOutputTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class InvokeModelWithResponseStreamResponseTypeDef(TypedDict):
    body: EventStream[ResponseStreamTypeDef]
    contentType: str
    performanceConfigLatency: PerformanceConfigLatencyType
    ResponseMetadata: ResponseMetadataTypeDef

ReasoningContentBlockUnionTypeDef = Union[
    ReasoningContentBlockTypeDef, ReasoningContentBlockOutputTypeDef
]

class ToolTypeDef(TypedDict):
    toolSpec: NotRequired[ToolSpecificationTypeDef]
    cachePoint: NotRequired[CachePointBlockTypeDef]

class ListAsyncInvokesResponseTypeDef(TypedDict):
    asyncInvokeSummaries: List[AsyncInvokeSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class InvokeModelWithBidirectionalStreamRequestTypeDef(TypedDict):
    modelId: str
    body: EventStream[InvokeModelWithBidirectionalStreamInputTypeDef]

GuardrailConverseImageBlockTypeDef = TypedDict(
    "GuardrailConverseImageBlockTypeDef",
    {
        "format": GuardrailConverseImageFormatType,
        "source": GuardrailConverseImageSourceUnionTypeDef,
    },
)

class GuardrailContentBlockTypeDef(TypedDict):
    text: NotRequired[GuardrailTextBlockTypeDef]
    image: NotRequired[GuardrailImageBlockTypeDef]

class CitationsContentBlockOutputTypeDef(TypedDict):
    content: NotRequired[List[CitationGeneratedContentTypeDef]]
    citations: NotRequired[List[CitationOutputTypeDef]]

CitationUnionTypeDef = Union[CitationTypeDef, CitationOutputTypeDef]

class ContentBlockDeltaTypeDef(TypedDict):
    text: NotRequired[str]
    toolUse: NotRequired[ToolUseBlockDeltaTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockDeltaTypeDef]
    citation: NotRequired[CitationsDeltaTypeDef]

DocumentBlockTypeDef = TypedDict(
    "DocumentBlockTypeDef",
    {
        "name": str,
        "source": DocumentSourceUnionTypeDef,
        "format": NotRequired[DocumentFormatType],
        "context": NotRequired[str],
        "citations": NotRequired[CitationsConfigTypeDef],
    },
)
ImageBlockTypeDef = TypedDict(
    "ImageBlockTypeDef",
    {
        "format": ImageFormatType,
        "source": ImageSourceUnionTypeDef,
    },
)

class ToolResultContentBlockOutputTypeDef(TypedDict):
    json: NotRequired[Dict[str, Any]]
    text: NotRequired[str]
    image: NotRequired[ImageBlockOutputTypeDef]
    document: NotRequired[DocumentBlockOutputTypeDef]
    video: NotRequired[VideoBlockOutputTypeDef]

VideoBlockTypeDef = TypedDict(
    "VideoBlockTypeDef",
    {
        "format": VideoFormatType,
        "source": VideoSourceUnionTypeDef,
    },
)

class GuardrailAutomatedReasoningTranslationAmbiguousFindingTypeDef(TypedDict):
    options: NotRequired[List[GuardrailAutomatedReasoningTranslationOptionTypeDef]]
    differenceScenarios: NotRequired[List[GuardrailAutomatedReasoningScenarioTypeDef]]

class ToolConfigurationTypeDef(TypedDict):
    tools: Sequence[ToolTypeDef]
    toolChoice: NotRequired[ToolChoiceTypeDef]

GuardrailConverseImageBlockUnionTypeDef = Union[
    GuardrailConverseImageBlockTypeDef, GuardrailConverseImageBlockOutputTypeDef
]

class ApplyGuardrailRequestTypeDef(TypedDict):
    guardrailIdentifier: str
    guardrailVersion: str
    source: GuardrailContentSourceType
    content: Sequence[GuardrailContentBlockTypeDef]
    outputScope: NotRequired[GuardrailOutputScopeType]

class CitationsContentBlockTypeDef(TypedDict):
    content: NotRequired[Sequence[CitationGeneratedContentTypeDef]]
    citations: NotRequired[Sequence[CitationUnionTypeDef]]

class ContentBlockDeltaEventTypeDef(TypedDict):
    delta: ContentBlockDeltaTypeDef
    contentBlockIndex: int

DocumentBlockUnionTypeDef = Union[DocumentBlockTypeDef, DocumentBlockOutputTypeDef]
ImageBlockUnionTypeDef = Union[ImageBlockTypeDef, ImageBlockOutputTypeDef]

class ToolResultBlockOutputTypeDef(TypedDict):
    toolUseId: str
    content: List[ToolResultContentBlockOutputTypeDef]
    status: NotRequired[ToolResultStatusType]

VideoBlockUnionTypeDef = Union[VideoBlockTypeDef, VideoBlockOutputTypeDef]

class GuardrailAutomatedReasoningFindingTypeDef(TypedDict):
    valid: NotRequired[GuardrailAutomatedReasoningValidFindingTypeDef]
    invalid: NotRequired[GuardrailAutomatedReasoningInvalidFindingTypeDef]
    satisfiable: NotRequired[GuardrailAutomatedReasoningSatisfiableFindingTypeDef]
    impossible: NotRequired[GuardrailAutomatedReasoningImpossibleFindingTypeDef]
    translationAmbiguous: NotRequired[GuardrailAutomatedReasoningTranslationAmbiguousFindingTypeDef]
    tooComplex: NotRequired[Dict[str, Any]]
    noTranslations: NotRequired[Dict[str, Any]]

class GuardrailConverseContentBlockTypeDef(TypedDict):
    text: NotRequired[GuardrailConverseTextBlockUnionTypeDef]
    image: NotRequired[GuardrailConverseImageBlockUnionTypeDef]

CitationsContentBlockUnionTypeDef = Union[
    CitationsContentBlockTypeDef, CitationsContentBlockOutputTypeDef
]

class ContentBlockOutputTypeDef(TypedDict):
    text: NotRequired[str]
    image: NotRequired[ImageBlockOutputTypeDef]
    document: NotRequired[DocumentBlockOutputTypeDef]
    video: NotRequired[VideoBlockOutputTypeDef]
    toolUse: NotRequired[ToolUseBlockOutputTypeDef]
    toolResult: NotRequired[ToolResultBlockOutputTypeDef]
    guardContent: NotRequired[GuardrailConverseContentBlockOutputTypeDef]
    cachePoint: NotRequired[CachePointBlockTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockOutputTypeDef]
    citationsContent: NotRequired[CitationsContentBlockOutputTypeDef]

class ToolResultContentBlockTypeDef(TypedDict):
    json: NotRequired[Mapping[str, Any]]
    text: NotRequired[str]
    image: NotRequired[ImageBlockUnionTypeDef]
    document: NotRequired[DocumentBlockUnionTypeDef]
    video: NotRequired[VideoBlockUnionTypeDef]

class GuardrailAutomatedReasoningPolicyAssessmentTypeDef(TypedDict):
    findings: NotRequired[List[GuardrailAutomatedReasoningFindingTypeDef]]

GuardrailConverseContentBlockUnionTypeDef = Union[
    GuardrailConverseContentBlockTypeDef, GuardrailConverseContentBlockOutputTypeDef
]

class MessageOutputTypeDef(TypedDict):
    role: ConversationRoleType
    content: List[ContentBlockOutputTypeDef]

ToolResultContentBlockUnionTypeDef = Union[
    ToolResultContentBlockTypeDef, ToolResultContentBlockOutputTypeDef
]

class GuardrailAssessmentTypeDef(TypedDict):
    topicPolicy: NotRequired[GuardrailTopicPolicyAssessmentTypeDef]
    contentPolicy: NotRequired[GuardrailContentPolicyAssessmentTypeDef]
    wordPolicy: NotRequired[GuardrailWordPolicyAssessmentTypeDef]
    sensitiveInformationPolicy: NotRequired[GuardrailSensitiveInformationPolicyAssessmentTypeDef]
    contextualGroundingPolicy: NotRequired[GuardrailContextualGroundingPolicyAssessmentTypeDef]
    automatedReasoningPolicy: NotRequired[GuardrailAutomatedReasoningPolicyAssessmentTypeDef]
    invocationMetrics: NotRequired[GuardrailInvocationMetricsTypeDef]

class SystemContentBlockTypeDef(TypedDict):
    text: NotRequired[str]
    guardContent: NotRequired[GuardrailConverseContentBlockUnionTypeDef]
    cachePoint: NotRequired[CachePointBlockTypeDef]

class ConverseOutputTypeDef(TypedDict):
    message: NotRequired[MessageOutputTypeDef]

class ToolResultBlockTypeDef(TypedDict):
    toolUseId: str
    content: Sequence[ToolResultContentBlockUnionTypeDef]
    status: NotRequired[ToolResultStatusType]

class ApplyGuardrailResponseTypeDef(TypedDict):
    usage: GuardrailUsageTypeDef
    action: GuardrailActionType
    actionReason: str
    outputs: List[GuardrailOutputContentTypeDef]
    assessments: List[GuardrailAssessmentTypeDef]
    guardrailCoverage: GuardrailCoverageTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GuardrailTraceAssessmentTypeDef(TypedDict):
    modelOutput: NotRequired[List[str]]
    inputAssessment: NotRequired[Dict[str, GuardrailAssessmentTypeDef]]
    outputAssessments: NotRequired[Dict[str, List[GuardrailAssessmentTypeDef]]]
    actionReason: NotRequired[str]

ToolResultBlockUnionTypeDef = Union[ToolResultBlockTypeDef, ToolResultBlockOutputTypeDef]

class ConverseStreamTraceTypeDef(TypedDict):
    guardrail: NotRequired[GuardrailTraceAssessmentTypeDef]
    promptRouter: NotRequired[PromptRouterTraceTypeDef]

class ConverseTraceTypeDef(TypedDict):
    guardrail: NotRequired[GuardrailTraceAssessmentTypeDef]
    promptRouter: NotRequired[PromptRouterTraceTypeDef]

class ContentBlockTypeDef(TypedDict):
    text: NotRequired[str]
    image: NotRequired[ImageBlockUnionTypeDef]
    document: NotRequired[DocumentBlockUnionTypeDef]
    video: NotRequired[VideoBlockUnionTypeDef]
    toolUse: NotRequired[ToolUseBlockUnionTypeDef]
    toolResult: NotRequired[ToolResultBlockUnionTypeDef]
    guardContent: NotRequired[GuardrailConverseContentBlockUnionTypeDef]
    cachePoint: NotRequired[CachePointBlockTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockUnionTypeDef]
    citationsContent: NotRequired[CitationsContentBlockUnionTypeDef]

class ConverseStreamMetadataEventTypeDef(TypedDict):
    usage: TokenUsageTypeDef
    metrics: ConverseStreamMetricsTypeDef
    trace: NotRequired[ConverseStreamTraceTypeDef]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class ConverseResponseTypeDef(TypedDict):
    output: ConverseOutputTypeDef
    stopReason: StopReasonType
    usage: TokenUsageTypeDef
    metrics: ConverseMetricsTypeDef
    additionalModelResponseFields: Dict[str, Any]
    trace: ConverseTraceTypeDef
    performanceConfig: PerformanceConfigurationTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

ContentBlockUnionTypeDef = Union[ContentBlockTypeDef, ContentBlockOutputTypeDef]

class ConverseStreamOutputTypeDef(TypedDict):
    messageStart: NotRequired[MessageStartEventTypeDef]
    contentBlockStart: NotRequired[ContentBlockStartEventTypeDef]
    contentBlockDelta: NotRequired[ContentBlockDeltaEventTypeDef]
    contentBlockStop: NotRequired[ContentBlockStopEventTypeDef]
    messageStop: NotRequired[MessageStopEventTypeDef]
    metadata: NotRequired[ConverseStreamMetadataEventTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    modelStreamErrorException: NotRequired[ModelStreamErrorExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    serviceUnavailableException: NotRequired[ServiceUnavailableExceptionTypeDef]

class MessageTypeDef(TypedDict):
    role: ConversationRoleType
    content: Sequence[ContentBlockUnionTypeDef]

class ConverseStreamResponseTypeDef(TypedDict):
    stream: EventStream[ConverseStreamOutputTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

MessageUnionTypeDef = Union[MessageTypeDef, MessageOutputTypeDef]

class ConverseRequestTypeDef(TypedDict):
    modelId: str
    messages: NotRequired[Sequence[MessageUnionTypeDef]]
    system: NotRequired[Sequence[SystemContentBlockTypeDef]]
    inferenceConfig: NotRequired[InferenceConfigurationTypeDef]
    toolConfig: NotRequired[ToolConfigurationTypeDef]
    guardrailConfig: NotRequired[GuardrailConfigurationTypeDef]
    additionalModelRequestFields: NotRequired[Mapping[str, Any]]
    promptVariables: NotRequired[Mapping[str, PromptVariableValuesTypeDef]]
    additionalModelResponseFieldPaths: NotRequired[Sequence[str]]
    requestMetadata: NotRequired[Mapping[str, str]]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class ConverseStreamRequestTypeDef(TypedDict):
    modelId: str
    messages: NotRequired[Sequence[MessageUnionTypeDef]]
    system: NotRequired[Sequence[SystemContentBlockTypeDef]]
    inferenceConfig: NotRequired[InferenceConfigurationTypeDef]
    toolConfig: NotRequired[ToolConfigurationTypeDef]
    guardrailConfig: NotRequired[GuardrailStreamConfigurationTypeDef]
    additionalModelRequestFields: NotRequired[Mapping[str, Any]]
    promptVariables: NotRequired[Mapping[str, PromptVariableValuesTypeDef]]
    additionalModelResponseFieldPaths: NotRequired[Sequence[str]]
    requestMetadata: NotRequired[Mapping[str, str]]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class ConverseTokensRequestTypeDef(TypedDict):
    messages: NotRequired[Sequence[MessageUnionTypeDef]]
    system: NotRequired[Sequence[SystemContentBlockTypeDef]]

class CountTokensInputTypeDef(TypedDict):
    invokeModel: NotRequired[InvokeModelTokensRequestTypeDef]
    converse: NotRequired[ConverseTokensRequestTypeDef]

CountTokensRequestTypeDef = TypedDict(
    "CountTokensRequestTypeDef",
    {
        "modelId": str,
        "input": CountTokensInputTypeDef,
    },
)
