# Copyright 2024 Cisco Systems, Inc. and its affiliates
from ipaddress import IPv4Address

from catalystwan.api.configuration_groups.parcel import Global, as_global, as_variable
from catalystwan.integration_tests.base import TestCaseBase, create_name_with_run_id
from catalystwan.integration_tests.test_data import bgp_parcel, ospf_parcel, ospfv3ipv4_parcel, ospfv3ipv6_parcel
from catalystwan.models.common import SubnetMask
from catalystwan.models.configuration.feature_profile.common import FeatureProfileCreationPayload
from catalystwan.models.configuration.feature_profile.sdwan.service.dhcp_server import (
    AddressPool,
    LanVpnDhcpServerParcel,
)
from catalystwan.models.configuration.feature_profile.sdwan.service.lan.ethernet import InterfaceEthernetParcel
from catalystwan.models.configuration.feature_profile.sdwan.service.lan.vpn import LanVpnParcel
from catalystwan.models.configuration.feature_profile.sdwan.trackers import Tracker, TrackerGroup


class TestServiceFeatureProfileBuilder(TestCaseBase):
    def setUp(self) -> None:
        self.fp_name = create_name_with_run_id("FeatureProfileBuilderService")
        self.fp_description = "Transport feature profile"
        self.builder = self.session.api.builders.feature_profiles.create_builder("service")
        self.builder.add_profile_name_and_description(
            feature_profile=FeatureProfileCreationPayload(name=self.fp_name, description=self.fp_description)
        )
        self.api = self.session.api.sdwan_feature_profiles.service

    def test_when_build_profile_with_vpn_and_interface_with_dhcp_expect_success(self):
        # Arrange
        service_vpn_parcel = LanVpnParcel(
            parcel_name="MinimumSpecifiedTransportVpnParcel",
            description="Description",
            vpn_id=as_global(50),
        )
        ethernet_parcel = InterfaceEthernetParcel(
            parcel_name="TestEthernetParcel",
            parcel_description="Test Ethernet Parcel",
            interface_name=as_global("HundredGigE"),
            ethernet_description=as_global("Test Ethernet Description"),
            shutdown=as_variable("{{vpn1_gi3_lan_ip_192.168.X.1/24_}}"),
        )
        dhcp_server_parcel = LanVpnDhcpServerParcel(
            parcel_name="DhcpServerDefault",
            parcel_description="Dhcp Server Parcel",
            address_pool=AddressPool(
                network_address=Global[IPv4Address](value=IPv4Address("10.0.0.2")),
                subnet_mask=Global[SubnetMask](value="255.255.255.255"),
            ),
        )
        vpn_tag = self.builder.add_parcel_vpn(service_vpn_parcel)
        self.builder.add_parcel_vpn_subparcel(vpn_tag, ethernet_parcel)
        self.builder.add_parcel_dhcp_server(ethernet_parcel.parcel_name, dhcp_server_parcel)
        # Act
        report = self.builder.build()
        # Assert
        assert len(report.failed_parcels) == 0

    def test_when_build_profile_with_vpn_and_routing_attached_expect_success(self):
        # Arrange
        service_vpn_parcel = LanVpnParcel(
            parcel_name="MinimumSpecifiedServiceVpnParcel",
            description="Description",
            vpn_id=as_global(50),
        )
        vpn_tag = self.builder.add_parcel_vpn(service_vpn_parcel)
        self.builder.add_parcel_routing_attached(vpn_tag, ospf_parcel)
        self.builder.add_parcel_routing_attached(vpn_tag, ospfv3ipv4_parcel)
        self.builder.add_parcel_routing_attached(vpn_tag, ospfv3ipv6_parcel)
        self.builder.add_parcel_routing_attached(vpn_tag, bgp_parcel)
        # Act
        report = self.builder.build()
        # Assert
        assert len(report.failed_parcels) == 0

    def test_when_vpn_interfaces_and_attached_tracker_expect_success(self):
        service_vpn_parcel = LanVpnParcel(
            parcel_name="MinimumSpecifiedTransportVpnParcel",
            description="Description",
            vpn_id=as_global(50),
        )
        ethernet_parcel = InterfaceEthernetParcel(
            parcel_name="TestEthernetParcel",
            parcel_description="Test Ethernet Parcel",
            interface_name=as_global("HundredGigE"),
            ethernet_description=as_global("Test Ethernet Description"),
            shutdown=as_variable("{{vpn1_gi3_lan_ip_192.168.X.1/24_}}"),
        )
        vpn_tag = self.builder.add_parcel_vpn(service_vpn_parcel)
        ethernet_tag = self.builder.add_parcel_vpn_subparcel(vpn_tag, ethernet_parcel)
        tracker = Tracker(
            parcel_name="TestTracker1",
            parcel_description="Test Tracker Description",
            tracker_name=Global[str](value="TestTracker1"),
            interval=Global[int](value=100),
            endpoint_api_url=Global[str](value="https://example.com/api"),
        )
        self.builder.add_tracker(associate_tags=[ethernet_tag], tracker=tracker)
        report = self.builder.build()

        assert len(report.failed_parcels) == 0

    def test_when_vpn_interfaces_and_attached_tracker_group_expect_success(self):
        service_vpn_parcel = LanVpnParcel(
            parcel_name="MinimumSpecifiedTransportVpnParcel",
            description="Description",
            vpn_id=as_global(50),
        )
        ethernet_parcel = InterfaceEthernetParcel(
            parcel_name="TestEthernetParcel",
            parcel_description="Test Ethernet Parcel",
            interface_name=as_global("HundredGigE"),
            ethernet_description=as_global("Test Ethernet Description"),
            shutdown=as_variable("{{vpn1_gi3_lan_ip_192.168.X.1/24_}}"),
        )
        vpn_tag = self.builder.add_parcel_vpn(service_vpn_parcel)
        ethernet_tag = self.builder.add_parcel_vpn_subparcel(vpn_tag, ethernet_parcel)
        tracker1 = Tracker(
            parcel_name="TestTracker1",
            parcel_description="Test Tracker Description",
            tracker_name=Global[str](value="TestTracker1"),
            interval=Global[int](value=100),
            endpoint_api_url=Global[str](value="https://example.com/api"),
        )
        tracker2 = Tracker(
            parcel_name="TestTracker2",
            parcel_description="Test Tracker Description",
            tracker_name=Global[str](value="TestTracker2"),
            interval=Global[int](value=100),
            endpoint_api_url=Global[str](value="https://example.com/api"),
        )
        tracker_group = TrackerGroup(
            parcel_name="TestTrackerGroup",
            parcel_description="Test Tracker Group Description",
            tracker_refs=[],
        )
        self.builder.add_tracker_group(
            associate_tags=[ethernet_tag], group=tracker_group, trackers=[tracker1, tracker2]
        )
        report = self.builder.build()

        assert len(report.failed_parcels) == 0

    def test_when_shared_tracker_expect_success(self):
        service_vpn_parcel = LanVpnParcel(
            parcel_name="MinimumSpecifiedTransportVpnParcel",
            description="Description",
            vpn_id=as_global(50),
        )
        ethernet_parcel_1 = InterfaceEthernetParcel(
            parcel_name="TestEthernetParcel1",
            parcel_description="Test Ethernet Parcel",
            interface_name=as_global("HundredGigE"),
            ethernet_description=as_global("Test Ethernet Description"),
            shutdown=as_variable("{{vpn1_gi3_lan_ip_192.168.X.1/24_}}"),
        )
        ethernet_parcel_2 = InterfaceEthernetParcel(
            parcel_name="TestEthernetParcel2",
            parcel_description="Test Ethernet Parcel",
            interface_name=as_global("HundredGigE"),
            ethernet_description=as_global("Test Ethernet Description"),
            shutdown=as_variable("{{vpn1_gi3_lan_ip_192.168.X.1/24_}}"),
        )
        vpn_tag = self.builder.add_parcel_vpn(service_vpn_parcel)
        ethernet_tag_1 = self.builder.add_parcel_vpn_subparcel(vpn_tag, ethernet_parcel_1)
        ethernet_tag_2 = self.builder.add_parcel_vpn_subparcel(vpn_tag, ethernet_parcel_2)
        tracker1 = Tracker(
            parcel_name="TestTracker1",
            parcel_description="Test Tracker Description",
            tracker_name=Global[str](value="TestTracker1"),
            interval=Global[int](value=100),
            endpoint_api_url=Global[str](value="https://example.com/api"),
        )
        tracker2 = Tracker(
            parcel_name="TestTracker2",
            parcel_description="Test Tracker Description",
            tracker_name=Global[str](value="TestTracker2"),
            interval=Global[int](value=100),
            endpoint_api_url=Global[str](value="https://example.com/api"),
        )
        tracker_group = TrackerGroup(
            parcel_name="TestTrackerGroup",
            parcel_description="Test Tracker Group Description",
            tracker_refs=[],
        )
        self.builder.add_tracker_group(
            associate_tags=[ethernet_tag_1], group=tracker_group, trackers=[tracker1, tracker2]
        )
        self.builder.add_tracker(associate_tags=[ethernet_tag_2], tracker=tracker2)
        report = self.builder.build()

        assert len(report.failed_parcels) == 0

    def tearDown(self) -> None:
        target_profile = self.api.get_profiles().filter(profile_name=self.fp_name).single_or_default()
        if target_profile:
            # In case of a failed test, the profile might not have been created
            self.api.delete_profile(target_profile.profile_id)
