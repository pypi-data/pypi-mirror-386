"""
Type annotations for bcm-recommended-actions service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bcm_recommended_actions/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_bcm_recommended_actions.client import BillingandCostManagementRecommendedActionsClient
    from types_boto3_bcm_recommended_actions.paginator import (
        ListRecommendedActionsPaginator,
    )

    session = Session()
    client: BillingandCostManagementRecommendedActionsClient = session.client("bcm-recommended-actions")

    list_recommended_actions_paginator: ListRecommendedActionsPaginator = client.get_paginator("list_recommended_actions")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    ListRecommendedActionsRequestPaginateTypeDef,
    ListRecommendedActionsResponseTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack


__all__ = ("ListRecommendedActionsPaginator",)


if TYPE_CHECKING:
    _ListRecommendedActionsPaginatorBase = Paginator[ListRecommendedActionsResponseTypeDef]
else:
    _ListRecommendedActionsPaginatorBase = Paginator  # type: ignore[assignment]


class ListRecommendedActionsPaginator(_ListRecommendedActionsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bcm-recommended-actions/paginator/ListRecommendedActions.html#BillingandCostManagementRecommendedActions.Paginator.ListRecommendedActions)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bcm_recommended_actions/paginators/#listrecommendedactionspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListRecommendedActionsRequestPaginateTypeDef]
    ) -> PageIterator[ListRecommendedActionsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bcm-recommended-actions/paginator/ListRecommendedActions.html#BillingandCostManagementRecommendedActions.Paginator.ListRecommendedActions.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bcm_recommended_actions/paginators/#listrecommendedactionspaginator)
        """
