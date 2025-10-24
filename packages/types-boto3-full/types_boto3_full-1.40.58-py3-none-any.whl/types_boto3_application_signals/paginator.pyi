"""
Type annotations for application-signals service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_application_signals.client import CloudWatchApplicationSignalsClient
    from types_boto3_application_signals.paginator import (
        ListServiceDependenciesPaginator,
        ListServiceDependentsPaginator,
        ListServiceLevelObjectiveExclusionWindowsPaginator,
        ListServiceLevelObjectivesPaginator,
        ListServiceOperationsPaginator,
        ListServiceStatesPaginator,
        ListServicesPaginator,
    )

    session = Session()
    client: CloudWatchApplicationSignalsClient = session.client("application-signals")

    list_service_dependencies_paginator: ListServiceDependenciesPaginator = client.get_paginator("list_service_dependencies")
    list_service_dependents_paginator: ListServiceDependentsPaginator = client.get_paginator("list_service_dependents")
    list_service_level_objective_exclusion_windows_paginator: ListServiceLevelObjectiveExclusionWindowsPaginator = client.get_paginator("list_service_level_objective_exclusion_windows")
    list_service_level_objectives_paginator: ListServiceLevelObjectivesPaginator = client.get_paginator("list_service_level_objectives")
    list_service_operations_paginator: ListServiceOperationsPaginator = client.get_paginator("list_service_operations")
    list_service_states_paginator: ListServiceStatesPaginator = client.get_paginator("list_service_states")
    list_services_paginator: ListServicesPaginator = client.get_paginator("list_services")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    ListServiceDependenciesInputPaginateTypeDef,
    ListServiceDependenciesOutputTypeDef,
    ListServiceDependentsInputPaginateTypeDef,
    ListServiceDependentsOutputTypeDef,
    ListServiceLevelObjectiveExclusionWindowsInputPaginateTypeDef,
    ListServiceLevelObjectiveExclusionWindowsOutputTypeDef,
    ListServiceLevelObjectivesInputPaginateTypeDef,
    ListServiceLevelObjectivesOutputTypeDef,
    ListServiceOperationsInputPaginateTypeDef,
    ListServiceOperationsOutputTypeDef,
    ListServicesInputPaginateTypeDef,
    ListServicesOutputTypeDef,
    ListServiceStatesInputPaginateTypeDef,
    ListServiceStatesOutputTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack

__all__ = (
    "ListServiceDependenciesPaginator",
    "ListServiceDependentsPaginator",
    "ListServiceLevelObjectiveExclusionWindowsPaginator",
    "ListServiceLevelObjectivesPaginator",
    "ListServiceOperationsPaginator",
    "ListServiceStatesPaginator",
    "ListServicesPaginator",
)

if TYPE_CHECKING:
    _ListServiceDependenciesPaginatorBase = Paginator[ListServiceDependenciesOutputTypeDef]
else:
    _ListServiceDependenciesPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceDependenciesPaginator(_ListServiceDependenciesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceDependencies.html#CloudWatchApplicationSignals.Paginator.ListServiceDependencies)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicedependenciespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceDependenciesInputPaginateTypeDef]
    ) -> PageIterator[ListServiceDependenciesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceDependencies.html#CloudWatchApplicationSignals.Paginator.ListServiceDependencies.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicedependenciespaginator)
        """

if TYPE_CHECKING:
    _ListServiceDependentsPaginatorBase = Paginator[ListServiceDependentsOutputTypeDef]
else:
    _ListServiceDependentsPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceDependentsPaginator(_ListServiceDependentsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceDependents.html#CloudWatchApplicationSignals.Paginator.ListServiceDependents)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicedependentspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceDependentsInputPaginateTypeDef]
    ) -> PageIterator[ListServiceDependentsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceDependents.html#CloudWatchApplicationSignals.Paginator.ListServiceDependents.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicedependentspaginator)
        """

if TYPE_CHECKING:
    _ListServiceLevelObjectiveExclusionWindowsPaginatorBase = Paginator[
        ListServiceLevelObjectiveExclusionWindowsOutputTypeDef
    ]
else:
    _ListServiceLevelObjectiveExclusionWindowsPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceLevelObjectiveExclusionWindowsPaginator(
    _ListServiceLevelObjectiveExclusionWindowsPaginatorBase
):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceLevelObjectiveExclusionWindows.html#CloudWatchApplicationSignals.Paginator.ListServiceLevelObjectiveExclusionWindows)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicelevelobjectiveexclusionwindowspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceLevelObjectiveExclusionWindowsInputPaginateTypeDef]
    ) -> PageIterator[ListServiceLevelObjectiveExclusionWindowsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceLevelObjectiveExclusionWindows.html#CloudWatchApplicationSignals.Paginator.ListServiceLevelObjectiveExclusionWindows.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicelevelobjectiveexclusionwindowspaginator)
        """

if TYPE_CHECKING:
    _ListServiceLevelObjectivesPaginatorBase = Paginator[ListServiceLevelObjectivesOutputTypeDef]
else:
    _ListServiceLevelObjectivesPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceLevelObjectivesPaginator(_ListServiceLevelObjectivesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceLevelObjectives.html#CloudWatchApplicationSignals.Paginator.ListServiceLevelObjectives)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicelevelobjectivespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceLevelObjectivesInputPaginateTypeDef]
    ) -> PageIterator[ListServiceLevelObjectivesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceLevelObjectives.html#CloudWatchApplicationSignals.Paginator.ListServiceLevelObjectives.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicelevelobjectivespaginator)
        """

if TYPE_CHECKING:
    _ListServiceOperationsPaginatorBase = Paginator[ListServiceOperationsOutputTypeDef]
else:
    _ListServiceOperationsPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceOperationsPaginator(_ListServiceOperationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceOperations.html#CloudWatchApplicationSignals.Paginator.ListServiceOperations)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listserviceoperationspaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceOperationsInputPaginateTypeDef]
    ) -> PageIterator[ListServiceOperationsOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceOperations.html#CloudWatchApplicationSignals.Paginator.ListServiceOperations.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listserviceoperationspaginator)
        """

if TYPE_CHECKING:
    _ListServiceStatesPaginatorBase = Paginator[ListServiceStatesOutputTypeDef]
else:
    _ListServiceStatesPaginatorBase = Paginator  # type: ignore[assignment]

class ListServiceStatesPaginator(_ListServiceStatesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceStates.html#CloudWatchApplicationSignals.Paginator.ListServiceStates)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicestatespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServiceStatesInputPaginateTypeDef]
    ) -> PageIterator[ListServiceStatesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServiceStates.html#CloudWatchApplicationSignals.Paginator.ListServiceStates.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicestatespaginator)
        """

if TYPE_CHECKING:
    _ListServicesPaginatorBase = Paginator[ListServicesOutputTypeDef]
else:
    _ListServicesPaginatorBase = Paginator  # type: ignore[assignment]

class ListServicesPaginator(_ListServicesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServices.html#CloudWatchApplicationSignals.Paginator.ListServices)
    [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicespaginator)
    """
    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListServicesInputPaginateTypeDef]
    ) -> PageIterator[ListServicesOutputTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/application-signals/paginator/ListServices.html#CloudWatchApplicationSignals.Paginator.ListServices.paginate)
        [Show types-boto3-full documentation](https://youtype.github.io/types_boto3_docs/types_boto3_application_signals/paginators/#listservicespaginator)
        """
