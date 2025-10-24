"""
Type annotations for waf service Client.

[Documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_waf.client import WAFClient

    session = Session()
    client: WAFClient = session.client("waf")
    ```
"""

from __future__ import annotations

import sys
from typing import Any, overload

from botocore.client import BaseClient, ClientMeta
from botocore.errorfactory import BaseClientExceptions
from botocore.exceptions import ClientError as BotocoreClientError

from .paginator import (
    GetRateBasedRuleManagedKeysPaginator,
    ListActivatedRulesInRuleGroupPaginator,
    ListByteMatchSetsPaginator,
    ListGeoMatchSetsPaginator,
    ListIPSetsPaginator,
    ListLoggingConfigurationsPaginator,
    ListRateBasedRulesPaginator,
    ListRegexMatchSetsPaginator,
    ListRegexPatternSetsPaginator,
    ListRuleGroupsPaginator,
    ListRulesPaginator,
    ListSizeConstraintSetsPaginator,
    ListSqlInjectionMatchSetsPaginator,
    ListSubscribedRuleGroupsPaginator,
    ListWebACLsPaginator,
    ListXssMatchSetsPaginator,
)
from .type_defs import (
    CreateByteMatchSetRequestTypeDef,
    CreateByteMatchSetResponseTypeDef,
    CreateGeoMatchSetRequestTypeDef,
    CreateGeoMatchSetResponseTypeDef,
    CreateIPSetRequestTypeDef,
    CreateIPSetResponseTypeDef,
    CreateRateBasedRuleRequestTypeDef,
    CreateRateBasedRuleResponseTypeDef,
    CreateRegexMatchSetRequestTypeDef,
    CreateRegexMatchSetResponseTypeDef,
    CreateRegexPatternSetRequestTypeDef,
    CreateRegexPatternSetResponseTypeDef,
    CreateRuleGroupRequestTypeDef,
    CreateRuleGroupResponseTypeDef,
    CreateRuleRequestTypeDef,
    CreateRuleResponseTypeDef,
    CreateSizeConstraintSetRequestTypeDef,
    CreateSizeConstraintSetResponseTypeDef,
    CreateSqlInjectionMatchSetRequestTypeDef,
    CreateSqlInjectionMatchSetResponseTypeDef,
    CreateWebACLMigrationStackRequestTypeDef,
    CreateWebACLMigrationStackResponseTypeDef,
    CreateWebACLRequestTypeDef,
    CreateWebACLResponseTypeDef,
    CreateXssMatchSetRequestTypeDef,
    CreateXssMatchSetResponseTypeDef,
    DeleteByteMatchSetRequestTypeDef,
    DeleteByteMatchSetResponseTypeDef,
    DeleteGeoMatchSetRequestTypeDef,
    DeleteGeoMatchSetResponseTypeDef,
    DeleteIPSetRequestTypeDef,
    DeleteIPSetResponseTypeDef,
    DeleteLoggingConfigurationRequestTypeDef,
    DeletePermissionPolicyRequestTypeDef,
    DeleteRateBasedRuleRequestTypeDef,
    DeleteRateBasedRuleResponseTypeDef,
    DeleteRegexMatchSetRequestTypeDef,
    DeleteRegexMatchSetResponseTypeDef,
    DeleteRegexPatternSetRequestTypeDef,
    DeleteRegexPatternSetResponseTypeDef,
    DeleteRuleGroupRequestTypeDef,
    DeleteRuleGroupResponseTypeDef,
    DeleteRuleRequestTypeDef,
    DeleteRuleResponseTypeDef,
    DeleteSizeConstraintSetRequestTypeDef,
    DeleteSizeConstraintSetResponseTypeDef,
    DeleteSqlInjectionMatchSetRequestTypeDef,
    DeleteSqlInjectionMatchSetResponseTypeDef,
    DeleteWebACLRequestTypeDef,
    DeleteWebACLResponseTypeDef,
    DeleteXssMatchSetRequestTypeDef,
    DeleteXssMatchSetResponseTypeDef,
    GetByteMatchSetRequestTypeDef,
    GetByteMatchSetResponseTypeDef,
    GetChangeTokenResponseTypeDef,
    GetChangeTokenStatusRequestTypeDef,
    GetChangeTokenStatusResponseTypeDef,
    GetGeoMatchSetRequestTypeDef,
    GetGeoMatchSetResponseTypeDef,
    GetIPSetRequestTypeDef,
    GetIPSetResponseTypeDef,
    GetLoggingConfigurationRequestTypeDef,
    GetLoggingConfigurationResponseTypeDef,
    GetPermissionPolicyRequestTypeDef,
    GetPermissionPolicyResponseTypeDef,
    GetRateBasedRuleManagedKeysRequestTypeDef,
    GetRateBasedRuleManagedKeysResponseTypeDef,
    GetRateBasedRuleRequestTypeDef,
    GetRateBasedRuleResponseTypeDef,
    GetRegexMatchSetRequestTypeDef,
    GetRegexMatchSetResponseTypeDef,
    GetRegexPatternSetRequestTypeDef,
    GetRegexPatternSetResponseTypeDef,
    GetRuleGroupRequestTypeDef,
    GetRuleGroupResponseTypeDef,
    GetRuleRequestTypeDef,
    GetRuleResponseTypeDef,
    GetSampledRequestsRequestTypeDef,
    GetSampledRequestsResponseTypeDef,
    GetSizeConstraintSetRequestTypeDef,
    GetSizeConstraintSetResponseTypeDef,
    GetSqlInjectionMatchSetRequestTypeDef,
    GetSqlInjectionMatchSetResponseTypeDef,
    GetWebACLRequestTypeDef,
    GetWebACLResponseTypeDef,
    GetXssMatchSetRequestTypeDef,
    GetXssMatchSetResponseTypeDef,
    ListActivatedRulesInRuleGroupRequestTypeDef,
    ListActivatedRulesInRuleGroupResponseTypeDef,
    ListByteMatchSetsRequestTypeDef,
    ListByteMatchSetsResponseTypeDef,
    ListGeoMatchSetsRequestTypeDef,
    ListGeoMatchSetsResponseTypeDef,
    ListIPSetsRequestTypeDef,
    ListIPSetsResponseTypeDef,
    ListLoggingConfigurationsRequestTypeDef,
    ListLoggingConfigurationsResponseTypeDef,
    ListRateBasedRulesRequestTypeDef,
    ListRateBasedRulesResponseTypeDef,
    ListRegexMatchSetsRequestTypeDef,
    ListRegexMatchSetsResponseTypeDef,
    ListRegexPatternSetsRequestTypeDef,
    ListRegexPatternSetsResponseTypeDef,
    ListRuleGroupsRequestTypeDef,
    ListRuleGroupsResponseTypeDef,
    ListRulesRequestTypeDef,
    ListRulesResponseTypeDef,
    ListSizeConstraintSetsRequestTypeDef,
    ListSizeConstraintSetsResponseTypeDef,
    ListSqlInjectionMatchSetsRequestTypeDef,
    ListSqlInjectionMatchSetsResponseTypeDef,
    ListSubscribedRuleGroupsRequestTypeDef,
    ListSubscribedRuleGroupsResponseTypeDef,
    ListTagsForResourceRequestTypeDef,
    ListTagsForResourceResponseTypeDef,
    ListWebACLsRequestTypeDef,
    ListWebACLsResponseTypeDef,
    ListXssMatchSetsRequestTypeDef,
    ListXssMatchSetsResponseTypeDef,
    PutLoggingConfigurationRequestTypeDef,
    PutLoggingConfigurationResponseTypeDef,
    PutPermissionPolicyRequestTypeDef,
    TagResourceRequestTypeDef,
    UntagResourceRequestTypeDef,
    UpdateByteMatchSetRequestTypeDef,
    UpdateByteMatchSetResponseTypeDef,
    UpdateGeoMatchSetRequestTypeDef,
    UpdateGeoMatchSetResponseTypeDef,
    UpdateIPSetRequestTypeDef,
    UpdateIPSetResponseTypeDef,
    UpdateRateBasedRuleRequestTypeDef,
    UpdateRateBasedRuleResponseTypeDef,
    UpdateRegexMatchSetRequestTypeDef,
    UpdateRegexMatchSetResponseTypeDef,
    UpdateRegexPatternSetRequestTypeDef,
    UpdateRegexPatternSetResponseTypeDef,
    UpdateRuleGroupRequestTypeDef,
    UpdateRuleGroupResponseTypeDef,
    UpdateRuleRequestTypeDef,
    UpdateRuleResponseTypeDef,
    UpdateSizeConstraintSetRequestTypeDef,
    UpdateSizeConstraintSetResponseTypeDef,
    UpdateSqlInjectionMatchSetRequestTypeDef,
    UpdateSqlInjectionMatchSetResponseTypeDef,
    UpdateWebACLRequestTypeDef,
    UpdateWebACLResponseTypeDef,
    UpdateXssMatchSetRequestTypeDef,
    UpdateXssMatchSetResponseTypeDef,
)

if sys.version_info >= (3, 9):
    from builtins import dict as Dict
    from builtins import type as Type
    from collections.abc import Mapping
else:
    from typing import Dict, Mapping, Type
if sys.version_info >= (3, 12):
    from typing import Literal, Unpack
else:
    from typing_extensions import Literal, Unpack

__all__ = ("WAFClient",)

class Exceptions(BaseClientExceptions):
    ClientError: Type[BotocoreClientError]
    WAFBadRequestException: Type[BotocoreClientError]
    WAFDisallowedNameException: Type[BotocoreClientError]
    WAFEntityMigrationException: Type[BotocoreClientError]
    WAFInternalErrorException: Type[BotocoreClientError]
    WAFInvalidAccountException: Type[BotocoreClientError]
    WAFInvalidOperationException: Type[BotocoreClientError]
    WAFInvalidParameterException: Type[BotocoreClientError]
    WAFInvalidPermissionPolicyException: Type[BotocoreClientError]
    WAFInvalidRegexPatternException: Type[BotocoreClientError]
    WAFLimitsExceededException: Type[BotocoreClientError]
    WAFNonEmptyEntityException: Type[BotocoreClientError]
    WAFNonexistentContainerException: Type[BotocoreClientError]
    WAFNonexistentItemException: Type[BotocoreClientError]
    WAFReferencedItemException: Type[BotocoreClientError]
    WAFServiceLinkedRoleErrorException: Type[BotocoreClientError]
    WAFStaleDataException: Type[BotocoreClientError]
    WAFSubscriptionNotFoundException: Type[BotocoreClientError]
    WAFTagOperationException: Type[BotocoreClientError]
    WAFTagOperationInternalErrorException: Type[BotocoreClientError]

class WAFClient(BaseClient):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf.html#WAF.Client)
    [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/)
    """

    meta: ClientMeta

    @property
    def exceptions(self) -> Exceptions:
        """
        WAFClient exceptions.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf.html#WAF.Client)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#exceptions)
        """

    def can_paginate(self, operation_name: str) -> bool:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/can_paginate.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#can_paginate)
        """

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Mapping[str, Any] = ...,
        ExpiresIn: int = 3600,
        HttpMethod: str = ...,
    ) -> str:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/generate_presigned_url.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#generate_presigned_url)
        """

    def create_byte_match_set(
        self, **kwargs: Unpack[CreateByteMatchSetRequestTypeDef]
    ) -> CreateByteMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_byte_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_byte_match_set)
        """

    def create_geo_match_set(
        self, **kwargs: Unpack[CreateGeoMatchSetRequestTypeDef]
    ) -> CreateGeoMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_geo_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_geo_match_set)
        """

    def create_ip_set(
        self, **kwargs: Unpack[CreateIPSetRequestTypeDef]
    ) -> CreateIPSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_ip_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_ip_set)
        """

    def create_rate_based_rule(
        self, **kwargs: Unpack[CreateRateBasedRuleRequestTypeDef]
    ) -> CreateRateBasedRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_rate_based_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_rate_based_rule)
        """

    def create_regex_match_set(
        self, **kwargs: Unpack[CreateRegexMatchSetRequestTypeDef]
    ) -> CreateRegexMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_regex_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_regex_match_set)
        """

    def create_regex_pattern_set(
        self, **kwargs: Unpack[CreateRegexPatternSetRequestTypeDef]
    ) -> CreateRegexPatternSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_regex_pattern_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_regex_pattern_set)
        """

    def create_rule(self, **kwargs: Unpack[CreateRuleRequestTypeDef]) -> CreateRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_rule)
        """

    def create_rule_group(
        self, **kwargs: Unpack[CreateRuleGroupRequestTypeDef]
    ) -> CreateRuleGroupResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_rule_group.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_rule_group)
        """

    def create_size_constraint_set(
        self, **kwargs: Unpack[CreateSizeConstraintSetRequestTypeDef]
    ) -> CreateSizeConstraintSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_size_constraint_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_size_constraint_set)
        """

    def create_sql_injection_match_set(
        self, **kwargs: Unpack[CreateSqlInjectionMatchSetRequestTypeDef]
    ) -> CreateSqlInjectionMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_sql_injection_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_sql_injection_match_set)
        """

    def create_web_acl(
        self, **kwargs: Unpack[CreateWebACLRequestTypeDef]
    ) -> CreateWebACLResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_web_acl.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_web_acl)
        """

    def create_web_acl_migration_stack(
        self, **kwargs: Unpack[CreateWebACLMigrationStackRequestTypeDef]
    ) -> CreateWebACLMigrationStackResponseTypeDef:
        """
        Creates an AWS CloudFormation WAFV2 template for the specified web ACL in the
        specified Amazon S3 bucket.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_web_acl_migration_stack.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_web_acl_migration_stack)
        """

    def create_xss_match_set(
        self, **kwargs: Unpack[CreateXssMatchSetRequestTypeDef]
    ) -> CreateXssMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/create_xss_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#create_xss_match_set)
        """

    def delete_byte_match_set(
        self, **kwargs: Unpack[DeleteByteMatchSetRequestTypeDef]
    ) -> DeleteByteMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_byte_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_byte_match_set)
        """

    def delete_geo_match_set(
        self, **kwargs: Unpack[DeleteGeoMatchSetRequestTypeDef]
    ) -> DeleteGeoMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_geo_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_geo_match_set)
        """

    def delete_ip_set(
        self, **kwargs: Unpack[DeleteIPSetRequestTypeDef]
    ) -> DeleteIPSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_ip_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_ip_set)
        """

    def delete_logging_configuration(
        self, **kwargs: Unpack[DeleteLoggingConfigurationRequestTypeDef]
    ) -> Dict[str, Any]:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_logging_configuration.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_logging_configuration)
        """

    def delete_permission_policy(
        self, **kwargs: Unpack[DeletePermissionPolicyRequestTypeDef]
    ) -> Dict[str, Any]:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_permission_policy.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_permission_policy)
        """

    def delete_rate_based_rule(
        self, **kwargs: Unpack[DeleteRateBasedRuleRequestTypeDef]
    ) -> DeleteRateBasedRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_rate_based_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_rate_based_rule)
        """

    def delete_regex_match_set(
        self, **kwargs: Unpack[DeleteRegexMatchSetRequestTypeDef]
    ) -> DeleteRegexMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_regex_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_regex_match_set)
        """

    def delete_regex_pattern_set(
        self, **kwargs: Unpack[DeleteRegexPatternSetRequestTypeDef]
    ) -> DeleteRegexPatternSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_regex_pattern_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_regex_pattern_set)
        """

    def delete_rule(self, **kwargs: Unpack[DeleteRuleRequestTypeDef]) -> DeleteRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_rule)
        """

    def delete_rule_group(
        self, **kwargs: Unpack[DeleteRuleGroupRequestTypeDef]
    ) -> DeleteRuleGroupResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_rule_group.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_rule_group)
        """

    def delete_size_constraint_set(
        self, **kwargs: Unpack[DeleteSizeConstraintSetRequestTypeDef]
    ) -> DeleteSizeConstraintSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_size_constraint_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_size_constraint_set)
        """

    def delete_sql_injection_match_set(
        self, **kwargs: Unpack[DeleteSqlInjectionMatchSetRequestTypeDef]
    ) -> DeleteSqlInjectionMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_sql_injection_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_sql_injection_match_set)
        """

    def delete_web_acl(
        self, **kwargs: Unpack[DeleteWebACLRequestTypeDef]
    ) -> DeleteWebACLResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_web_acl.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_web_acl)
        """

    def delete_xss_match_set(
        self, **kwargs: Unpack[DeleteXssMatchSetRequestTypeDef]
    ) -> DeleteXssMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/delete_xss_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#delete_xss_match_set)
        """

    def get_byte_match_set(
        self, **kwargs: Unpack[GetByteMatchSetRequestTypeDef]
    ) -> GetByteMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_byte_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_byte_match_set)
        """

    def get_change_token(self) -> GetChangeTokenResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_change_token.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_change_token)
        """

    def get_change_token_status(
        self, **kwargs: Unpack[GetChangeTokenStatusRequestTypeDef]
    ) -> GetChangeTokenStatusResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_change_token_status.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_change_token_status)
        """

    def get_geo_match_set(
        self, **kwargs: Unpack[GetGeoMatchSetRequestTypeDef]
    ) -> GetGeoMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_geo_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_geo_match_set)
        """

    def get_ip_set(self, **kwargs: Unpack[GetIPSetRequestTypeDef]) -> GetIPSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_ip_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_ip_set)
        """

    def get_logging_configuration(
        self, **kwargs: Unpack[GetLoggingConfigurationRequestTypeDef]
    ) -> GetLoggingConfigurationResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_logging_configuration.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_logging_configuration)
        """

    def get_permission_policy(
        self, **kwargs: Unpack[GetPermissionPolicyRequestTypeDef]
    ) -> GetPermissionPolicyResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_permission_policy.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_permission_policy)
        """

    def get_rate_based_rule(
        self, **kwargs: Unpack[GetRateBasedRuleRequestTypeDef]
    ) -> GetRateBasedRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_rate_based_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_rate_based_rule)
        """

    def get_rate_based_rule_managed_keys(
        self, **kwargs: Unpack[GetRateBasedRuleManagedKeysRequestTypeDef]
    ) -> GetRateBasedRuleManagedKeysResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_rate_based_rule_managed_keys.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_rate_based_rule_managed_keys)
        """

    def get_regex_match_set(
        self, **kwargs: Unpack[GetRegexMatchSetRequestTypeDef]
    ) -> GetRegexMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_regex_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_regex_match_set)
        """

    def get_regex_pattern_set(
        self, **kwargs: Unpack[GetRegexPatternSetRequestTypeDef]
    ) -> GetRegexPatternSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_regex_pattern_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_regex_pattern_set)
        """

    def get_rule(self, **kwargs: Unpack[GetRuleRequestTypeDef]) -> GetRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_rule)
        """

    def get_rule_group(
        self, **kwargs: Unpack[GetRuleGroupRequestTypeDef]
    ) -> GetRuleGroupResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_rule_group.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_rule_group)
        """

    def get_sampled_requests(
        self, **kwargs: Unpack[GetSampledRequestsRequestTypeDef]
    ) -> GetSampledRequestsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_sampled_requests.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_sampled_requests)
        """

    def get_size_constraint_set(
        self, **kwargs: Unpack[GetSizeConstraintSetRequestTypeDef]
    ) -> GetSizeConstraintSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_size_constraint_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_size_constraint_set)
        """

    def get_sql_injection_match_set(
        self, **kwargs: Unpack[GetSqlInjectionMatchSetRequestTypeDef]
    ) -> GetSqlInjectionMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_sql_injection_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_sql_injection_match_set)
        """

    def get_web_acl(self, **kwargs: Unpack[GetWebACLRequestTypeDef]) -> GetWebACLResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_web_acl.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_web_acl)
        """

    def get_xss_match_set(
        self, **kwargs: Unpack[GetXssMatchSetRequestTypeDef]
    ) -> GetXssMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_xss_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_xss_match_set)
        """

    def list_activated_rules_in_rule_group(
        self, **kwargs: Unpack[ListActivatedRulesInRuleGroupRequestTypeDef]
    ) -> ListActivatedRulesInRuleGroupResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_activated_rules_in_rule_group.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_activated_rules_in_rule_group)
        """

    def list_byte_match_sets(
        self, **kwargs: Unpack[ListByteMatchSetsRequestTypeDef]
    ) -> ListByteMatchSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_byte_match_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_byte_match_sets)
        """

    def list_geo_match_sets(
        self, **kwargs: Unpack[ListGeoMatchSetsRequestTypeDef]
    ) -> ListGeoMatchSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_geo_match_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_geo_match_sets)
        """

    def list_ip_sets(self, **kwargs: Unpack[ListIPSetsRequestTypeDef]) -> ListIPSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_ip_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_ip_sets)
        """

    def list_logging_configurations(
        self, **kwargs: Unpack[ListLoggingConfigurationsRequestTypeDef]
    ) -> ListLoggingConfigurationsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_logging_configurations.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_logging_configurations)
        """

    def list_rate_based_rules(
        self, **kwargs: Unpack[ListRateBasedRulesRequestTypeDef]
    ) -> ListRateBasedRulesResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_rate_based_rules.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_rate_based_rules)
        """

    def list_regex_match_sets(
        self, **kwargs: Unpack[ListRegexMatchSetsRequestTypeDef]
    ) -> ListRegexMatchSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_regex_match_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_regex_match_sets)
        """

    def list_regex_pattern_sets(
        self, **kwargs: Unpack[ListRegexPatternSetsRequestTypeDef]
    ) -> ListRegexPatternSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_regex_pattern_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_regex_pattern_sets)
        """

    def list_rule_groups(
        self, **kwargs: Unpack[ListRuleGroupsRequestTypeDef]
    ) -> ListRuleGroupsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_rule_groups.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_rule_groups)
        """

    def list_rules(self, **kwargs: Unpack[ListRulesRequestTypeDef]) -> ListRulesResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_rules.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_rules)
        """

    def list_size_constraint_sets(
        self, **kwargs: Unpack[ListSizeConstraintSetsRequestTypeDef]
    ) -> ListSizeConstraintSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_size_constraint_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_size_constraint_sets)
        """

    def list_sql_injection_match_sets(
        self, **kwargs: Unpack[ListSqlInjectionMatchSetsRequestTypeDef]
    ) -> ListSqlInjectionMatchSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_sql_injection_match_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_sql_injection_match_sets)
        """

    def list_subscribed_rule_groups(
        self, **kwargs: Unpack[ListSubscribedRuleGroupsRequestTypeDef]
    ) -> ListSubscribedRuleGroupsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_subscribed_rule_groups.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_subscribed_rule_groups)
        """

    def list_tags_for_resource(
        self, **kwargs: Unpack[ListTagsForResourceRequestTypeDef]
    ) -> ListTagsForResourceResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_tags_for_resource.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_tags_for_resource)
        """

    def list_web_acls(
        self, **kwargs: Unpack[ListWebACLsRequestTypeDef]
    ) -> ListWebACLsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_web_acls.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_web_acls)
        """

    def list_xss_match_sets(
        self, **kwargs: Unpack[ListXssMatchSetsRequestTypeDef]
    ) -> ListXssMatchSetsResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/list_xss_match_sets.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#list_xss_match_sets)
        """

    def put_logging_configuration(
        self, **kwargs: Unpack[PutLoggingConfigurationRequestTypeDef]
    ) -> PutLoggingConfigurationResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/put_logging_configuration.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#put_logging_configuration)
        """

    def put_permission_policy(
        self, **kwargs: Unpack[PutPermissionPolicyRequestTypeDef]
    ) -> Dict[str, Any]:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/put_permission_policy.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#put_permission_policy)
        """

    def tag_resource(self, **kwargs: Unpack[TagResourceRequestTypeDef]) -> Dict[str, Any]:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/tag_resource.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#tag_resource)
        """

    def untag_resource(self, **kwargs: Unpack[UntagResourceRequestTypeDef]) -> Dict[str, Any]:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/untag_resource.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#untag_resource)
        """

    def update_byte_match_set(
        self, **kwargs: Unpack[UpdateByteMatchSetRequestTypeDef]
    ) -> UpdateByteMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_byte_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_byte_match_set)
        """

    def update_geo_match_set(
        self, **kwargs: Unpack[UpdateGeoMatchSetRequestTypeDef]
    ) -> UpdateGeoMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_geo_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_geo_match_set)
        """

    def update_ip_set(
        self, **kwargs: Unpack[UpdateIPSetRequestTypeDef]
    ) -> UpdateIPSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_ip_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_ip_set)
        """

    def update_rate_based_rule(
        self, **kwargs: Unpack[UpdateRateBasedRuleRequestTypeDef]
    ) -> UpdateRateBasedRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_rate_based_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_rate_based_rule)
        """

    def update_regex_match_set(
        self, **kwargs: Unpack[UpdateRegexMatchSetRequestTypeDef]
    ) -> UpdateRegexMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_regex_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_regex_match_set)
        """

    def update_regex_pattern_set(
        self, **kwargs: Unpack[UpdateRegexPatternSetRequestTypeDef]
    ) -> UpdateRegexPatternSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_regex_pattern_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_regex_pattern_set)
        """

    def update_rule(self, **kwargs: Unpack[UpdateRuleRequestTypeDef]) -> UpdateRuleResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_rule.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_rule)
        """

    def update_rule_group(
        self, **kwargs: Unpack[UpdateRuleGroupRequestTypeDef]
    ) -> UpdateRuleGroupResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_rule_group.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_rule_group)
        """

    def update_size_constraint_set(
        self, **kwargs: Unpack[UpdateSizeConstraintSetRequestTypeDef]
    ) -> UpdateSizeConstraintSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_size_constraint_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_size_constraint_set)
        """

    def update_sql_injection_match_set(
        self, **kwargs: Unpack[UpdateSqlInjectionMatchSetRequestTypeDef]
    ) -> UpdateSqlInjectionMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_sql_injection_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_sql_injection_match_set)
        """

    def update_web_acl(
        self, **kwargs: Unpack[UpdateWebACLRequestTypeDef]
    ) -> UpdateWebACLResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_web_acl.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_web_acl)
        """

    def update_xss_match_set(
        self, **kwargs: Unpack[UpdateXssMatchSetRequestTypeDef]
    ) -> UpdateXssMatchSetResponseTypeDef:
        """
        This is <b>AWS WAF Classic</b> documentation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/update_xss_match_set.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#update_xss_match_set)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["get_rate_based_rule_managed_keys"]
    ) -> GetRateBasedRuleManagedKeysPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_activated_rules_in_rule_group"]
    ) -> ListActivatedRulesInRuleGroupPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_byte_match_sets"]
    ) -> ListByteMatchSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_geo_match_sets"]
    ) -> ListGeoMatchSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_ip_sets"]
    ) -> ListIPSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_logging_configurations"]
    ) -> ListLoggingConfigurationsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_rate_based_rules"]
    ) -> ListRateBasedRulesPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_regex_match_sets"]
    ) -> ListRegexMatchSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_regex_pattern_sets"]
    ) -> ListRegexPatternSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_rule_groups"]
    ) -> ListRuleGroupsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_rules"]
    ) -> ListRulesPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_size_constraint_sets"]
    ) -> ListSizeConstraintSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_sql_injection_match_sets"]
    ) -> ListSqlInjectionMatchSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_subscribed_rule_groups"]
    ) -> ListSubscribedRuleGroupsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_web_acls"]
    ) -> ListWebACLsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """

    @overload  # type: ignore[override]
    def get_paginator(  # type: ignore[override]
        self, operation_name: Literal["list_xss_match_sets"]
    ) -> ListXssMatchSetsPaginator:
        """
        Create a paginator for an operation.

        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/waf/client/get_paginator.html)
        [Show boto3-stubs-full documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/client/#get_paginator)
        """
