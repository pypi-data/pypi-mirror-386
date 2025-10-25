"""
Type annotations for controltower service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_controltower.client import ControlTowerClient
    from types_boto3_controltower.paginator import (
        ListBaselinesPaginator,
        ListControlOperationsPaginator,
        ListEnabledBaselinesPaginator,
        ListEnabledControlsPaginator,
        ListLandingZoneOperationsPaginator,
        ListLandingZonesPaginator,
    )

    session = Session()
    client: ControlTowerClient = session.client("controltower")

    list_baselines_paginator: ListBaselinesPaginator = client.get_paginator("list_baselines")
    list_control_operations_paginator: ListControlOperationsPaginator = client.get_paginator("list_control_operations")
    list_enabled_baselines_paginator: ListEnabledBaselinesPaginator = client.get_paginator("list_enabled_baselines")
    list_enabled_controls_paginator: ListEnabledControlsPaginator = client.get_paginator("list_enabled_controls")
    list_landing_zone_operations_paginator: ListLandingZoneOperationsPaginator = client.get_paginator("list_landing_zone_operations")
    list_landing_zones_paginator: ListLandingZonesPaginator = client.get_paginator("list_landing_zones")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    ListBaselinesInputPaginateTypeDef,
    ListBaselinesOutputTypeDef,
    ListControlOperationsInputPaginateTypeDef,
    ListControlOperationsOutputTypeDef,
    ListEnabledBaselinesInputPaginateTypeDef,
    ListEnabledBaselinesOutputTypeDef,
    ListEnabledControlsInputPaginateTypeDef,
    ListEnabledControlsOutputTypeDef,
    ListLandingZoneOperationsInputPaginateTypeDef,
    ListLandingZoneOperationsOutputTypeDef,
    ListLandingZonesInputPaginateTypeDef,
    ListLandingZonesOutputTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack


__all__ = (
    "ListBaselinesPaginator",
    "ListControlOperationsPaginator",
    "ListEnabledBaselinesPaginator",
    "ListEnabledControlsPaginator",
    "ListLandingZoneOperationsPaginator",
    "ListLandingZonesPaginator",
)


if TYPE_CHECKING:
    _ListBaselinesPaginatorBase = Paginator[ListBaselinesOutputTypeDef]
else:
    _ListBaselinesPaginatorBase = Paginator  # type: ignore[assignment]


class ListBaselinesPaginator(_ListBaselinesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListBaselines.html#ControlTower.Paginator.ListBaselines)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listbaselinespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListBaselinesInputPaginateTypeDef]
    ) -> PageIterator[ListBaselinesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListBaselines.html#ControlTower.Paginator.ListBaselines.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listbaselinespaginator)
        """


if TYPE_CHECKING:
    _ListControlOperationsPaginatorBase = Paginator[ListControlOperationsOutputTypeDef]
else:
    _ListControlOperationsPaginatorBase = Paginator  # type: ignore[assignment]


class ListControlOperationsPaginator(_ListControlOperationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListControlOperations.html#ControlTower.Paginator.ListControlOperations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listcontroloperationspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListControlOperationsInputPaginateTypeDef]
    ) -> PageIterator[ListControlOperationsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListControlOperations.html#ControlTower.Paginator.ListControlOperations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listcontroloperationspaginator)
        """


if TYPE_CHECKING:
    _ListEnabledBaselinesPaginatorBase = Paginator[ListEnabledBaselinesOutputTypeDef]
else:
    _ListEnabledBaselinesPaginatorBase = Paginator  # type: ignore[assignment]


class ListEnabledBaselinesPaginator(_ListEnabledBaselinesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListEnabledBaselines.html#ControlTower.Paginator.ListEnabledBaselines)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listenabledbaselinespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListEnabledBaselinesInputPaginateTypeDef]
    ) -> PageIterator[ListEnabledBaselinesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListEnabledBaselines.html#ControlTower.Paginator.ListEnabledBaselines.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listenabledbaselinespaginator)
        """


if TYPE_CHECKING:
    _ListEnabledControlsPaginatorBase = Paginator[ListEnabledControlsOutputTypeDef]
else:
    _ListEnabledControlsPaginatorBase = Paginator  # type: ignore[assignment]


class ListEnabledControlsPaginator(_ListEnabledControlsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListEnabledControls.html#ControlTower.Paginator.ListEnabledControls)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listenabledcontrolspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListEnabledControlsInputPaginateTypeDef]
    ) -> PageIterator[ListEnabledControlsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListEnabledControls.html#ControlTower.Paginator.ListEnabledControls.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listenabledcontrolspaginator)
        """


if TYPE_CHECKING:
    _ListLandingZoneOperationsPaginatorBase = Paginator[ListLandingZoneOperationsOutputTypeDef]
else:
    _ListLandingZoneOperationsPaginatorBase = Paginator  # type: ignore[assignment]


class ListLandingZoneOperationsPaginator(_ListLandingZoneOperationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListLandingZoneOperations.html#ControlTower.Paginator.ListLandingZoneOperations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listlandingzoneoperationspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListLandingZoneOperationsInputPaginateTypeDef]
    ) -> PageIterator[ListLandingZoneOperationsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListLandingZoneOperations.html#ControlTower.Paginator.ListLandingZoneOperations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listlandingzoneoperationspaginator)
        """


if TYPE_CHECKING:
    _ListLandingZonesPaginatorBase = Paginator[ListLandingZonesOutputTypeDef]
else:
    _ListLandingZonesPaginatorBase = Paginator  # type: ignore[assignment]


class ListLandingZonesPaginator(_ListLandingZonesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListLandingZones.html#ControlTower.Paginator.ListLandingZones)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listlandingzonespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListLandingZonesInputPaginateTypeDef]
    ) -> PageIterator[ListLandingZonesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/controltower/paginator/ListLandingZones.html#ControlTower.Paginator.ListLandingZones.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_controltower/paginators/#listlandingzonespaginator)
        """
