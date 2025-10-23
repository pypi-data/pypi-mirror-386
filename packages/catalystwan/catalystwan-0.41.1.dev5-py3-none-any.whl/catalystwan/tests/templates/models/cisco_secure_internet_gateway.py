# Copyright 2024 Cisco Systems, Inc. and its affiliates
from ipaddress import IPv4Address, IPv4Interface

from catalystwan.api.templates.models.cisco_secure_internet_gateway import (
    CiscoSecureInternetGatewayModel,
    Interface,
    InterfacePair,
    Service,
    Tracker,
)

cisco_sig = CiscoSecureInternetGatewayModel(
    template_name="cisco_sig",
    template_description="Comprehensive CiscoSecureInternetGateway Configuration",
    vpn_id=10,
    child_org_id="example_org",
    interface=[
        Interface(
            if_name="ipsec255",
            auto=True,
            shutdown=False,
            description="Main interface for SIG",
            unnumbered=False,
            address=IPv4Interface("192.168.1.1/24"),
            tunnel_source=IPv4Address("192.168.1.1"),
            tunnel_source_interface="Loopback0",
            tunnel_route_via="192.168.2.1",
            tunnel_destination="203.0.113.1",
            application="sig",
            tunnel_set="secure-internet-gateway-umbrella",
            tunnel_dc_preference="primary-dc",
            tcp_mss_adjust=1400,
            mtu=1400,
            dpd_interval=30,
            dpd_retries=3,
            ike_version=2,
            pre_shared_secret="MyPreSharedSecret",  # pragma: allowlist secret
            ike_rekey_interval=3600,
            ike_ciphersuite="aes256-cbc-sha1",
            ike_group="14",
            pre_shared_key_dynamic=False,
            ike_local_id="local-id",
            ike_remote_id="remote-id",
            ipsec_rekey_interval=3600,
            ipsec_replay_window=32,
            ipsec_ciphersuite="aes256-gcm",
            perfect_forward_secrecy="group-14",
            tracker=True,
            track_enable=True,
        )
    ],
    service=[
        Service(
            svc_type="sig",
            interface_pair=[
                InterfacePair(
                    active_interface="GigabitEthernet0/0",
                    active_interface_weight=10,
                    backup_interface="GigabitEthernet0/1",
                    backup_interface_weight=5,
                )
            ],
            auth_required=True,
            xff_forward_enabled=True,
            ofw_enabled=False,
            ips_control=True,
            caution_enabled=False,
            primary_data_center="Auto",
            secondary_data_center="Auto",
            ip=True,
            idle_time=30,
            display_time_unit="MINUTE",
            ip_enforced_for_known_browsers=True,
            refresh_time=5,
            refresh_time_unit="MINUTE",
            enabled=True,
            block_internet_until_accepted=False,
            force_ssl_inspection=True,
            timeout=60,
            data_center_primary="Auto",
            data_center_secondary="Auto",
        )
    ],
    tracker_src_ip=IPv4Interface("192.0.2.1/32"),
    tracker=[
        Tracker(
            name="health-check-tracker",
            endpoint_api_url="http://api.example.com/health",
            threshold=100,
            interval=60,
            multiplier=2,
            tracker_type="SIG",
        )
    ],
)
