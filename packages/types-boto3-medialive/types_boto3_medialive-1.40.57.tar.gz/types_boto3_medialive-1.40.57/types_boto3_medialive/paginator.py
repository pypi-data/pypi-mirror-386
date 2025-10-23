"""
Type annotations for medialive service client paginators.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from boto3.session import Session

    from types_boto3_medialive.client import MediaLiveClient
    from types_boto3_medialive.paginator import (
        DescribeSchedulePaginator,
        ListAlertsPaginator,
        ListChannelPlacementGroupsPaginator,
        ListChannelsPaginator,
        ListCloudWatchAlarmTemplateGroupsPaginator,
        ListCloudWatchAlarmTemplatesPaginator,
        ListClusterAlertsPaginator,
        ListClustersPaginator,
        ListEventBridgeRuleTemplateGroupsPaginator,
        ListEventBridgeRuleTemplatesPaginator,
        ListInputDeviceTransfersPaginator,
        ListInputDevicesPaginator,
        ListInputSecurityGroupsPaginator,
        ListInputsPaginator,
        ListMultiplexAlertsPaginator,
        ListMultiplexProgramsPaginator,
        ListMultiplexesPaginator,
        ListNetworksPaginator,
        ListNodesPaginator,
        ListOfferingsPaginator,
        ListReservationsPaginator,
        ListSdiSourcesPaginator,
        ListSignalMapsPaginator,
    )

    session = Session()
    client: MediaLiveClient = session.client("medialive")

    describe_schedule_paginator: DescribeSchedulePaginator = client.get_paginator("describe_schedule")
    list_alerts_paginator: ListAlertsPaginator = client.get_paginator("list_alerts")
    list_channel_placement_groups_paginator: ListChannelPlacementGroupsPaginator = client.get_paginator("list_channel_placement_groups")
    list_channels_paginator: ListChannelsPaginator = client.get_paginator("list_channels")
    list_cloud_watch_alarm_template_groups_paginator: ListCloudWatchAlarmTemplateGroupsPaginator = client.get_paginator("list_cloud_watch_alarm_template_groups")
    list_cloud_watch_alarm_templates_paginator: ListCloudWatchAlarmTemplatesPaginator = client.get_paginator("list_cloud_watch_alarm_templates")
    list_cluster_alerts_paginator: ListClusterAlertsPaginator = client.get_paginator("list_cluster_alerts")
    list_clusters_paginator: ListClustersPaginator = client.get_paginator("list_clusters")
    list_event_bridge_rule_template_groups_paginator: ListEventBridgeRuleTemplateGroupsPaginator = client.get_paginator("list_event_bridge_rule_template_groups")
    list_event_bridge_rule_templates_paginator: ListEventBridgeRuleTemplatesPaginator = client.get_paginator("list_event_bridge_rule_templates")
    list_input_device_transfers_paginator: ListInputDeviceTransfersPaginator = client.get_paginator("list_input_device_transfers")
    list_input_devices_paginator: ListInputDevicesPaginator = client.get_paginator("list_input_devices")
    list_input_security_groups_paginator: ListInputSecurityGroupsPaginator = client.get_paginator("list_input_security_groups")
    list_inputs_paginator: ListInputsPaginator = client.get_paginator("list_inputs")
    list_multiplex_alerts_paginator: ListMultiplexAlertsPaginator = client.get_paginator("list_multiplex_alerts")
    list_multiplex_programs_paginator: ListMultiplexProgramsPaginator = client.get_paginator("list_multiplex_programs")
    list_multiplexes_paginator: ListMultiplexesPaginator = client.get_paginator("list_multiplexes")
    list_networks_paginator: ListNetworksPaginator = client.get_paginator("list_networks")
    list_nodes_paginator: ListNodesPaginator = client.get_paginator("list_nodes")
    list_offerings_paginator: ListOfferingsPaginator = client.get_paginator("list_offerings")
    list_reservations_paginator: ListReservationsPaginator = client.get_paginator("list_reservations")
    list_sdi_sources_paginator: ListSdiSourcesPaginator = client.get_paginator("list_sdi_sources")
    list_signal_maps_paginator: ListSignalMapsPaginator = client.get_paginator("list_signal_maps")
    ```
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from botocore.paginate import PageIterator, Paginator

from .type_defs import (
    DescribeScheduleRequestPaginateTypeDef,
    DescribeScheduleResponseTypeDef,
    ListAlertsRequestPaginateTypeDef,
    ListAlertsResponseTypeDef,
    ListChannelPlacementGroupsRequestPaginateTypeDef,
    ListChannelPlacementGroupsResponseTypeDef,
    ListChannelsRequestPaginateTypeDef,
    ListChannelsResponseTypeDef,
    ListCloudWatchAlarmTemplateGroupsRequestPaginateTypeDef,
    ListCloudWatchAlarmTemplateGroupsResponseTypeDef,
    ListCloudWatchAlarmTemplatesRequestPaginateTypeDef,
    ListCloudWatchAlarmTemplatesResponseTypeDef,
    ListClusterAlertsRequestPaginateTypeDef,
    ListClusterAlertsResponseTypeDef,
    ListClustersRequestPaginateTypeDef,
    ListClustersResponseTypeDef,
    ListEventBridgeRuleTemplateGroupsRequestPaginateTypeDef,
    ListEventBridgeRuleTemplateGroupsResponseTypeDef,
    ListEventBridgeRuleTemplatesRequestPaginateTypeDef,
    ListEventBridgeRuleTemplatesResponseTypeDef,
    ListInputDevicesRequestPaginateTypeDef,
    ListInputDevicesResponseTypeDef,
    ListInputDeviceTransfersRequestPaginateTypeDef,
    ListInputDeviceTransfersResponseTypeDef,
    ListInputSecurityGroupsRequestPaginateTypeDef,
    ListInputSecurityGroupsResponseTypeDef,
    ListInputsRequestPaginateTypeDef,
    ListInputsResponseTypeDef,
    ListMultiplexAlertsRequestPaginateTypeDef,
    ListMultiplexAlertsResponseTypeDef,
    ListMultiplexesRequestPaginateTypeDef,
    ListMultiplexesResponseTypeDef,
    ListMultiplexProgramsRequestPaginateTypeDef,
    ListMultiplexProgramsResponseTypeDef,
    ListNetworksRequestPaginateTypeDef,
    ListNetworksResponseTypeDef,
    ListNodesRequestPaginateTypeDef,
    ListNodesResponseTypeDef,
    ListOfferingsRequestPaginateTypeDef,
    ListOfferingsResponseTypeDef,
    ListReservationsRequestPaginateTypeDef,
    ListReservationsResponseTypeDef,
    ListSdiSourcesRequestPaginateTypeDef,
    ListSdiSourcesResponseTypeDef,
    ListSignalMapsRequestPaginateTypeDef,
    ListSignalMapsResponseTypeDef,
)

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack


__all__ = (
    "DescribeSchedulePaginator",
    "ListAlertsPaginator",
    "ListChannelPlacementGroupsPaginator",
    "ListChannelsPaginator",
    "ListCloudWatchAlarmTemplateGroupsPaginator",
    "ListCloudWatchAlarmTemplatesPaginator",
    "ListClusterAlertsPaginator",
    "ListClustersPaginator",
    "ListEventBridgeRuleTemplateGroupsPaginator",
    "ListEventBridgeRuleTemplatesPaginator",
    "ListInputDeviceTransfersPaginator",
    "ListInputDevicesPaginator",
    "ListInputSecurityGroupsPaginator",
    "ListInputsPaginator",
    "ListMultiplexAlertsPaginator",
    "ListMultiplexProgramsPaginator",
    "ListMultiplexesPaginator",
    "ListNetworksPaginator",
    "ListNodesPaginator",
    "ListOfferingsPaginator",
    "ListReservationsPaginator",
    "ListSdiSourcesPaginator",
    "ListSignalMapsPaginator",
)


if TYPE_CHECKING:
    _DescribeSchedulePaginatorBase = Paginator[DescribeScheduleResponseTypeDef]
else:
    _DescribeSchedulePaginatorBase = Paginator  # type: ignore[assignment]


class DescribeSchedulePaginator(_DescribeSchedulePaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/DescribeSchedule.html#MediaLive.Paginator.DescribeSchedule)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#describeschedulepaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[DescribeScheduleRequestPaginateTypeDef]
    ) -> PageIterator[DescribeScheduleResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/DescribeSchedule.html#MediaLive.Paginator.DescribeSchedule.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#describeschedulepaginator)
        """


if TYPE_CHECKING:
    _ListAlertsPaginatorBase = Paginator[ListAlertsResponseTypeDef]
else:
    _ListAlertsPaginatorBase = Paginator  # type: ignore[assignment]


class ListAlertsPaginator(_ListAlertsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListAlerts.html#MediaLive.Paginator.ListAlerts)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listalertspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListAlertsRequestPaginateTypeDef]
    ) -> PageIterator[ListAlertsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListAlerts.html#MediaLive.Paginator.ListAlerts.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listalertspaginator)
        """


if TYPE_CHECKING:
    _ListChannelPlacementGroupsPaginatorBase = Paginator[ListChannelPlacementGroupsResponseTypeDef]
else:
    _ListChannelPlacementGroupsPaginatorBase = Paginator  # type: ignore[assignment]


class ListChannelPlacementGroupsPaginator(_ListChannelPlacementGroupsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListChannelPlacementGroups.html#MediaLive.Paginator.ListChannelPlacementGroups)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listchannelplacementgroupspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListChannelPlacementGroupsRequestPaginateTypeDef]
    ) -> PageIterator[ListChannelPlacementGroupsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListChannelPlacementGroups.html#MediaLive.Paginator.ListChannelPlacementGroups.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listchannelplacementgroupspaginator)
        """


if TYPE_CHECKING:
    _ListChannelsPaginatorBase = Paginator[ListChannelsResponseTypeDef]
else:
    _ListChannelsPaginatorBase = Paginator  # type: ignore[assignment]


class ListChannelsPaginator(_ListChannelsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListChannels.html#MediaLive.Paginator.ListChannels)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listchannelspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListChannelsRequestPaginateTypeDef]
    ) -> PageIterator[ListChannelsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListChannels.html#MediaLive.Paginator.ListChannels.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listchannelspaginator)
        """


if TYPE_CHECKING:
    _ListCloudWatchAlarmTemplateGroupsPaginatorBase = Paginator[
        ListCloudWatchAlarmTemplateGroupsResponseTypeDef
    ]
else:
    _ListCloudWatchAlarmTemplateGroupsPaginatorBase = Paginator  # type: ignore[assignment]


class ListCloudWatchAlarmTemplateGroupsPaginator(_ListCloudWatchAlarmTemplateGroupsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListCloudWatchAlarmTemplateGroups.html#MediaLive.Paginator.ListCloudWatchAlarmTemplateGroups)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listcloudwatchalarmtemplategroupspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListCloudWatchAlarmTemplateGroupsRequestPaginateTypeDef]
    ) -> PageIterator[ListCloudWatchAlarmTemplateGroupsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListCloudWatchAlarmTemplateGroups.html#MediaLive.Paginator.ListCloudWatchAlarmTemplateGroups.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listcloudwatchalarmtemplategroupspaginator)
        """


if TYPE_CHECKING:
    _ListCloudWatchAlarmTemplatesPaginatorBase = Paginator[
        ListCloudWatchAlarmTemplatesResponseTypeDef
    ]
else:
    _ListCloudWatchAlarmTemplatesPaginatorBase = Paginator  # type: ignore[assignment]


class ListCloudWatchAlarmTemplatesPaginator(_ListCloudWatchAlarmTemplatesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListCloudWatchAlarmTemplates.html#MediaLive.Paginator.ListCloudWatchAlarmTemplates)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listcloudwatchalarmtemplatespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListCloudWatchAlarmTemplatesRequestPaginateTypeDef]
    ) -> PageIterator[ListCloudWatchAlarmTemplatesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListCloudWatchAlarmTemplates.html#MediaLive.Paginator.ListCloudWatchAlarmTemplates.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listcloudwatchalarmtemplatespaginator)
        """


if TYPE_CHECKING:
    _ListClusterAlertsPaginatorBase = Paginator[ListClusterAlertsResponseTypeDef]
else:
    _ListClusterAlertsPaginatorBase = Paginator  # type: ignore[assignment]


class ListClusterAlertsPaginator(_ListClusterAlertsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListClusterAlerts.html#MediaLive.Paginator.ListClusterAlerts)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listclusteralertspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListClusterAlertsRequestPaginateTypeDef]
    ) -> PageIterator[ListClusterAlertsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListClusterAlerts.html#MediaLive.Paginator.ListClusterAlerts.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listclusteralertspaginator)
        """


if TYPE_CHECKING:
    _ListClustersPaginatorBase = Paginator[ListClustersResponseTypeDef]
else:
    _ListClustersPaginatorBase = Paginator  # type: ignore[assignment]


class ListClustersPaginator(_ListClustersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListClusters.html#MediaLive.Paginator.ListClusters)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listclusterspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListClustersRequestPaginateTypeDef]
    ) -> PageIterator[ListClustersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListClusters.html#MediaLive.Paginator.ListClusters.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listclusterspaginator)
        """


if TYPE_CHECKING:
    _ListEventBridgeRuleTemplateGroupsPaginatorBase = Paginator[
        ListEventBridgeRuleTemplateGroupsResponseTypeDef
    ]
else:
    _ListEventBridgeRuleTemplateGroupsPaginatorBase = Paginator  # type: ignore[assignment]


class ListEventBridgeRuleTemplateGroupsPaginator(_ListEventBridgeRuleTemplateGroupsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListEventBridgeRuleTemplateGroups.html#MediaLive.Paginator.ListEventBridgeRuleTemplateGroups)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listeventbridgeruletemplategroupspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListEventBridgeRuleTemplateGroupsRequestPaginateTypeDef]
    ) -> PageIterator[ListEventBridgeRuleTemplateGroupsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListEventBridgeRuleTemplateGroups.html#MediaLive.Paginator.ListEventBridgeRuleTemplateGroups.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listeventbridgeruletemplategroupspaginator)
        """


if TYPE_CHECKING:
    _ListEventBridgeRuleTemplatesPaginatorBase = Paginator[
        ListEventBridgeRuleTemplatesResponseTypeDef
    ]
else:
    _ListEventBridgeRuleTemplatesPaginatorBase = Paginator  # type: ignore[assignment]


class ListEventBridgeRuleTemplatesPaginator(_ListEventBridgeRuleTemplatesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListEventBridgeRuleTemplates.html#MediaLive.Paginator.ListEventBridgeRuleTemplates)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listeventbridgeruletemplatespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListEventBridgeRuleTemplatesRequestPaginateTypeDef]
    ) -> PageIterator[ListEventBridgeRuleTemplatesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListEventBridgeRuleTemplates.html#MediaLive.Paginator.ListEventBridgeRuleTemplates.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listeventbridgeruletemplatespaginator)
        """


if TYPE_CHECKING:
    _ListInputDeviceTransfersPaginatorBase = Paginator[ListInputDeviceTransfersResponseTypeDef]
else:
    _ListInputDeviceTransfersPaginatorBase = Paginator  # type: ignore[assignment]


class ListInputDeviceTransfersPaginator(_ListInputDeviceTransfersPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputDeviceTransfers.html#MediaLive.Paginator.ListInputDeviceTransfers)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputdevicetransferspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListInputDeviceTransfersRequestPaginateTypeDef]
    ) -> PageIterator[ListInputDeviceTransfersResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputDeviceTransfers.html#MediaLive.Paginator.ListInputDeviceTransfers.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputdevicetransferspaginator)
        """


if TYPE_CHECKING:
    _ListInputDevicesPaginatorBase = Paginator[ListInputDevicesResponseTypeDef]
else:
    _ListInputDevicesPaginatorBase = Paginator  # type: ignore[assignment]


class ListInputDevicesPaginator(_ListInputDevicesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputDevices.html#MediaLive.Paginator.ListInputDevices)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputdevicespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListInputDevicesRequestPaginateTypeDef]
    ) -> PageIterator[ListInputDevicesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputDevices.html#MediaLive.Paginator.ListInputDevices.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputdevicespaginator)
        """


if TYPE_CHECKING:
    _ListInputSecurityGroupsPaginatorBase = Paginator[ListInputSecurityGroupsResponseTypeDef]
else:
    _ListInputSecurityGroupsPaginatorBase = Paginator  # type: ignore[assignment]


class ListInputSecurityGroupsPaginator(_ListInputSecurityGroupsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputSecurityGroups.html#MediaLive.Paginator.ListInputSecurityGroups)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputsecuritygroupspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListInputSecurityGroupsRequestPaginateTypeDef]
    ) -> PageIterator[ListInputSecurityGroupsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputSecurityGroups.html#MediaLive.Paginator.ListInputSecurityGroups.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputsecuritygroupspaginator)
        """


if TYPE_CHECKING:
    _ListInputsPaginatorBase = Paginator[ListInputsResponseTypeDef]
else:
    _ListInputsPaginatorBase = Paginator  # type: ignore[assignment]


class ListInputsPaginator(_ListInputsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputs.html#MediaLive.Paginator.ListInputs)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListInputsRequestPaginateTypeDef]
    ) -> PageIterator[ListInputsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListInputs.html#MediaLive.Paginator.ListInputs.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listinputspaginator)
        """


if TYPE_CHECKING:
    _ListMultiplexAlertsPaginatorBase = Paginator[ListMultiplexAlertsResponseTypeDef]
else:
    _ListMultiplexAlertsPaginatorBase = Paginator  # type: ignore[assignment]


class ListMultiplexAlertsPaginator(_ListMultiplexAlertsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexAlerts.html#MediaLive.Paginator.ListMultiplexAlerts)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexalertspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListMultiplexAlertsRequestPaginateTypeDef]
    ) -> PageIterator[ListMultiplexAlertsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexAlerts.html#MediaLive.Paginator.ListMultiplexAlerts.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexalertspaginator)
        """


if TYPE_CHECKING:
    _ListMultiplexProgramsPaginatorBase = Paginator[ListMultiplexProgramsResponseTypeDef]
else:
    _ListMultiplexProgramsPaginatorBase = Paginator  # type: ignore[assignment]


class ListMultiplexProgramsPaginator(_ListMultiplexProgramsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexPrograms.html#MediaLive.Paginator.ListMultiplexPrograms)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexprogramspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListMultiplexProgramsRequestPaginateTypeDef]
    ) -> PageIterator[ListMultiplexProgramsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexPrograms.html#MediaLive.Paginator.ListMultiplexPrograms.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexprogramspaginator)
        """


if TYPE_CHECKING:
    _ListMultiplexesPaginatorBase = Paginator[ListMultiplexesResponseTypeDef]
else:
    _ListMultiplexesPaginatorBase = Paginator  # type: ignore[assignment]


class ListMultiplexesPaginator(_ListMultiplexesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexes.html#MediaLive.Paginator.ListMultiplexes)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListMultiplexesRequestPaginateTypeDef]
    ) -> PageIterator[ListMultiplexesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListMultiplexes.html#MediaLive.Paginator.ListMultiplexes.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listmultiplexespaginator)
        """


if TYPE_CHECKING:
    _ListNetworksPaginatorBase = Paginator[ListNetworksResponseTypeDef]
else:
    _ListNetworksPaginatorBase = Paginator  # type: ignore[assignment]


class ListNetworksPaginator(_ListNetworksPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListNetworks.html#MediaLive.Paginator.ListNetworks)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listnetworkspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListNetworksRequestPaginateTypeDef]
    ) -> PageIterator[ListNetworksResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListNetworks.html#MediaLive.Paginator.ListNetworks.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listnetworkspaginator)
        """


if TYPE_CHECKING:
    _ListNodesPaginatorBase = Paginator[ListNodesResponseTypeDef]
else:
    _ListNodesPaginatorBase = Paginator  # type: ignore[assignment]


class ListNodesPaginator(_ListNodesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListNodes.html#MediaLive.Paginator.ListNodes)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listnodespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListNodesRequestPaginateTypeDef]
    ) -> PageIterator[ListNodesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListNodes.html#MediaLive.Paginator.ListNodes.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listnodespaginator)
        """


if TYPE_CHECKING:
    _ListOfferingsPaginatorBase = Paginator[ListOfferingsResponseTypeDef]
else:
    _ListOfferingsPaginatorBase = Paginator  # type: ignore[assignment]


class ListOfferingsPaginator(_ListOfferingsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListOfferings.html#MediaLive.Paginator.ListOfferings)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listofferingspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListOfferingsRequestPaginateTypeDef]
    ) -> PageIterator[ListOfferingsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListOfferings.html#MediaLive.Paginator.ListOfferings.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listofferingspaginator)
        """


if TYPE_CHECKING:
    _ListReservationsPaginatorBase = Paginator[ListReservationsResponseTypeDef]
else:
    _ListReservationsPaginatorBase = Paginator  # type: ignore[assignment]


class ListReservationsPaginator(_ListReservationsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListReservations.html#MediaLive.Paginator.ListReservations)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listreservationspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListReservationsRequestPaginateTypeDef]
    ) -> PageIterator[ListReservationsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListReservations.html#MediaLive.Paginator.ListReservations.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listreservationspaginator)
        """


if TYPE_CHECKING:
    _ListSdiSourcesPaginatorBase = Paginator[ListSdiSourcesResponseTypeDef]
else:
    _ListSdiSourcesPaginatorBase = Paginator  # type: ignore[assignment]


class ListSdiSourcesPaginator(_ListSdiSourcesPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListSdiSources.html#MediaLive.Paginator.ListSdiSources)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listsdisourcespaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListSdiSourcesRequestPaginateTypeDef]
    ) -> PageIterator[ListSdiSourcesResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListSdiSources.html#MediaLive.Paginator.ListSdiSources.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listsdisourcespaginator)
        """


if TYPE_CHECKING:
    _ListSignalMapsPaginatorBase = Paginator[ListSignalMapsResponseTypeDef]
else:
    _ListSignalMapsPaginatorBase = Paginator  # type: ignore[assignment]


class ListSignalMapsPaginator(_ListSignalMapsPaginatorBase):
    """
    [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListSignalMaps.html#MediaLive.Paginator.ListSignalMaps)
    [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listsignalmapspaginator)
    """

    def paginate(  # type: ignore[override]
        self, **kwargs: Unpack[ListSignalMapsRequestPaginateTypeDef]
    ) -> PageIterator[ListSignalMapsResponseTypeDef]:
        """
        [Show boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/medialive/paginator/ListSignalMaps.html#MediaLive.Paginator.ListSignalMaps.paginate)
        [Show types-boto3 documentation](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/paginators/#listsignalmapspaginator)
        """
