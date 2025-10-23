# Copyright 2024 Cisco Systems, Inc. and its affiliates

from ipaddress import IPv4Address
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from typing_extensions import Annotated

from catalystwan.api.configuration_groups.parcel import Default, Global, Variable, _ParcelBase
from catalystwan.models.common import EthernetDuplexMode, MediaType, VersionedField
from catalystwan.models.configuration.feature_profile.common import (
    Arp,
    DynamicDhcpDistance,
    EthernetNatAttributesIpv4,
    InterfaceDynamicIPv4Address,
    InterfaceDynamicIPv6Address,
    InterfaceStaticIPv4Address,
    RefIdItem,
    StaticIPv4Address,
    StaticIPv4AddressConfig,
    StaticIPv6Address,
)
from catalystwan.models.configuration.feature_profile.sdwan.service.lan.common import (
    VrrpIPv6Address,
    VrrpTrackingObject,
)

LoadBalance = Literal[
    "flow",
    "vlan",
]

LacpMode = Literal[
    "active",
    "passive",
]


LacpRate = Literal[
    "fast",
    "normal",
]


class PortChannelMemberLinksLacp(BaseModel):
    lacp_mode: Union[Global[LacpMode], Default[Literal["active"]], Variable] = Field(
        validation_alias="lacpMode", serialization_alias="lacpMode"
    )
    interface: Optional[RefIdItem] = Field(default=None)
    lacp_port_priority: Optional[Union[Variable, Global[int], Default[None]]] = Field(
        default=None, validation_alias="lacpPortPriority", serialization_alias="lacpPortPriority"
    )
    lacp_rate: Optional[Union[Variable, Global[LacpRate], Default[None]]] = Field(
        default=None, validation_alias="lacpRate", serialization_alias="lacpRate"
    )


class LacpModeMainInterface(BaseModel):
    port_channel_member_links: List[PortChannelMemberLinksLacp] = Field(
        validation_alias="portChannelMemberLinks",
        serialization_alias="portChannelMemberLinks",
        description="Configure Port-Channel member links",
    )
    lacp_fast_switchover: Optional[Union[Global[bool], Default[bool], Variable]] = Field(
        default=None, validation_alias="lacpFastSwitchover", serialization_alias="lacpFastSwitchover"
    )
    lacp_max_bundle: Optional[Union[Variable, Global[int], Default[None]]] = Field(
        default=None, validation_alias="lacpMaxBundle", serialization_alias="lacpMaxBundle"
    )
    lacp_min_bundle: Optional[Union[Variable, Global[int], Default[None]]] = Field(
        default=None, validation_alias="lacpMinBundle", serialization_alias="lacpMinBundle"
    )
    load_balance: Optional[Union[Variable, Global[LoadBalance], Default[None]]] = Field(
        default=None, validation_alias="loadBalance", serialization_alias="loadBalance"
    )
    port_channel_qos_aggregate: Optional[Union[Global[bool], Default[bool], Variable]] = Field(
        default=None, validation_alias="portChannelQosAggregate", serialization_alias="portChannelQosAggregate"
    )


class MainInterfaceLcap(BaseModel):
    lacp_mode_main_interface: LacpModeMainInterface = Field(
        validation_alias="lacpModeMainInterface", serialization_alias="lacpModeMainInterface"
    )


class PortChannelMemberLinksMain(BaseModel):
    interface: Optional[RefIdItem] = Field(default=None)


class StaticModeMainInterface(BaseModel):
    port_channel_member_links: List[PortChannelMemberLinksMain] = Field(
        validation_alias="portChannelMemberLinks",
        serialization_alias="portChannelMemberLinks",
        description="Configure Port-Channel member links",
    )
    load_balance: Optional[Union[Variable, Global[LoadBalance], Default[None]]] = Field(
        default=None, validation_alias="loadBalance", serialization_alias="loadBalance"
    )
    port_channel_qos_aggregate: Optional[Union[Global[bool], Default[bool], Variable]] = Field(
        default=None, validation_alias="portChannelQosAggregate", serialization_alias="portChannelQosAggregate"
    )


class MainInterfaceStatic(BaseModel):
    static_mode_main_interface: StaticModeMainInterface = Field(
        validation_alias="staticModeMainInterface", serialization_alias="staticModeMainInterface"
    )


MainInterface = Union[MainInterfaceLcap, MainInterfaceStatic]


class PortChannelMainIntf(BaseModel):
    main_interface: MainInterface = Field(validation_alias="mainInterface", serialization_alias="mainInterface")


class SubInterface(BaseModel):
    primary_interface_name: Optional[Union[Global[str], Variable, Default[None]]] = Field(
        default=None, validation_alias="primaryInterfaceName", serialization_alias="primaryInterfaceName"
    )
    secondary_interface_name: Optional[Union[Global[str], Variable, Default[None]]] = Field(
        default=None, validation_alias="secondaryInterfaceName", serialization_alias="secondaryInterfaceName"
    )


class PortChannelSubIntf(BaseModel):
    sub_interface: SubInterface = Field(validation_alias="subInterface", serialization_alias="subInterface")


PortChannel = Union[PortChannelSubIntf, PortChannelMainIntf]


class Dhcpv6Helper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    ip_address: Union[Global[str], Variable] = Field(serialization_alias="ipAddress", validation_alias="ipAddress")
    vpn: Optional[Union[Global[int], Variable, Default[None]]] = None


class StaticIPv6AddressConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    primary_ip_address: StaticIPv6Address = Field(
        serialization_alias="primaryIpV6Address", validation_alias="primaryIpV6Address"
    )
    secondary_ip_address: Optional[List[StaticIPv6Address]] = Field(
        serialization_alias="secondaryIpV6Address", validation_alias="secondaryIpV6Address", default=None
    )
    dhcp_helper_v6: Optional[List[Dhcpv6Helper]] = Field(
        serialization_alias="dhcpHelperV6", validation_alias="dhcpHelperV6", default=None
    )


class InterfaceStaticIPv6Address(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    static: StaticIPv6AddressConfig


class NatAttributesIPv6(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    nat64: Optional[Union[Global[bool], Default[bool]]] = Default[bool](value=False)


class AclQos(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    shaping_rate: Optional[Union[Global[int], Variable, Default[None]]] = Field(
        serialization_alias="shapingRate", validation_alias="shapingRate", default=None
    )
    ipv4_acl_egress: Optional[RefIdItem] = Field(
        serialization_alias="ipv4AclEgress", validation_alias="ipv4AclEgress", default=None
    )
    ipv4_acl_ingress: Optional[RefIdItem] = Field(
        serialization_alias="ipv4AclIngress", validation_alias="ipv4AclIngress", default=None
    )
    ipv6_acl_egress: Optional[RefIdItem] = Field(
        serialization_alias="ipv6AclEgress", validation_alias="ipv6AclEgress", default=None
    )
    ipv6_acl_ingress: Optional[RefIdItem] = Field(
        serialization_alias="ipv6AclIngress", validation_alias="ipv6AclIngress", default=None
    )


class VrrpIPv6(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    group_id: Union[Variable, Global[int]] = Field(serialization_alias="groupId", validation_alias="groupId")
    priority: Union[Variable, Global[int], Default[int]] = Default[int](value=100)
    timer: Union[Variable, Global[int], Default[int]] = Default[int](value=1000)
    track_omp: Union[Global[bool], Default[bool]] = Field(
        serialization_alias="trackOmp", validation_alias="trackOmp", default=Default[bool](value=False)
    )
    ipv6: List[VrrpIPv6Address]
    follow_dual_router_h_a_availability: Optional[Union[Global[bool], Default[bool]]] = Field(
        default=None,
        validation_alias="followDualRouterHAAvailability",
        serialization_alias="followDualRouterHAAvailability",
    )
    min_preempt_delay: Optional[Union[Variable, Global[int], Default[None]]] = Field(
        default=None, validation_alias="minPreemptDelay", serialization_alias="minPreemptDelay"
    )


class VrrpIPv4(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    group_id: Union[Variable, Global[int]]
    priority: Union[Variable, Global[int], Default[int]] = Default[int](value=100)
    timer: Union[Variable, Global[int], Default[int]] = Default[int](value=1000)
    track_omp: Union[Global[bool], Default[bool]] = Field(
        serialization_alias="trackOmp", validation_alias="trackOmp", default=Default[bool](value=False)
    )
    ip_address: Union[Global[str], Global[IPv4Address], Variable] = Field(
        serialization_alias="ipAddress", validation_alias="ipAddress"
    )
    ip_address_secondary: Optional[List[StaticIPv4Address]] = Field(
        serialization_alias="ipAddressSecondary",
        validation_alias="ipAddressSecondary",
        default=None,
    )
    tloc_pref_change: Union[Global[bool], Default[bool]] = Field(
        serialization_alias="tlocPrefChange", validation_alias="tlocPrefChange", default=Default[bool](value=False)
    )
    tloc_pref_change_value: Optional[Union[Global[int], Default[None]]] = Field(
        serialization_alias="tlocPrefChangeValue", validation_alias="tlocPrefChangeValue", default=None
    )
    tracking_object: Optional[List[VrrpTrackingObject]] = Field(
        serialization_alias="trackingObject", validation_alias="trackingObject", default=None
    )
    follow_dual_router_h_a_availability: Optional[Union[Global[bool], Default[bool]]] = Field(
        default=None,
        validation_alias="followDualRouterHAAvailability",
        serialization_alias="followDualRouterHAAvailability",
    )
    min_preempt_delay: Optional[Union[Variable, Global[int], Default[None]]] = Field(
        default=None, validation_alias="minPreemptDelay", serialization_alias="minPreemptDelay"
    )

    @model_serializer(mode="wrap", when_used="json")
    def serialize(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Dict[str, Any]:
        return VersionedField.dump(self.model_fields, handler(self), info)


class Trustsec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    enable_sgt_propogation: Union[Global[bool], Default[bool]] = Field(
        serialization_alias="enableSGTPropogation",
        validation_alias="enableSGTPropogation",
        default=Default[bool](value=False),
    )
    propogate: Annotated[
        Optional[Union[Global[bool], Default[bool]]], VersionedField(versions="<=20.12", forbidden=True)
    ] = Default[bool](value=True)
    security_group_tag: Optional[Union[Global[int], Variable, Default[None]]] = Field(
        serialization_alias="securityGroupTag", validation_alias="securityGroupTag", default=None
    )
    enable_enforced_propogation: Union[Global[bool], Default[None]] = Field(
        default=Default[None](value=None),
        serialization_alias="enableEnforcedPropogation",
        validation_alias="enableEnforcedPropogation",
    )
    enforced_security_group_tag: Union[Global[int], Variable, Default[None]] = Field(
        default=Default[None](value=None),
        serialization_alias="enforcedSecurityGroupTag",
        validation_alias="enforcedSecurityGroupTag",
    )

    @model_serializer(mode="wrap", when_used="json")
    def serialize(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Dict[str, Any]:
        return VersionedField.dump(self.model_fields, handler(self), info)


class AdvancedEthernetAttributes(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    duplex: Optional[Union[Global[EthernetDuplexMode], Variable, Default[None]]] = None
    mac_address: Optional[Union[Global[str], Variable, Default[None]]] = Field(
        serialization_alias="macAddress", validation_alias="macAddress", default=None
    )
    ip_mtu: Union[Global[int], Variable, Default[int]] = Field(
        serialization_alias="ipMtu", validation_alias="ipMtu", default=Default[int](value=1500)
    )
    interface_mtu: Optional[Union[Global[int], Variable, Default[int]]] = Field(
        default=None, serialization_alias="intrfMtu", validation_alias="intrfMtu"
    )
    tcp_mss: Optional[Union[Global[int], Variable, Default[int]]] = Field(
        serialization_alias="tcpMss", validation_alias="tcpMss", default=None
    )
    speed: Optional[Union[Global[str], Variable, Default[None]]] = None
    arp_timeout: Union[Global[int], Variable, Default[int]] = Field(
        serialization_alias="arpTimeout", validation_alias="arpTimeout", default=Default[int](value=1200)
    )
    autonegotiate: Optional[Union[Global[bool], Variable, Default[bool]]] = None
    media_type: Optional[Union[Global[MediaType], Variable, Default[None]]] = Field(
        serialization_alias="mediaType", validation_alias="mediaType", default=None
    )
    load_interval: Union[Global[int], Variable, Default[int]] = Field(
        serialization_alias="loadInterval", validation_alias="loadInterval", default=Default[int](value=30)
    )
    tracker: Optional[Union[Global[str], Variable, Default[None]]] = None
    icmp_redirect_disable: Optional[Union[Global[bool], Variable, Default[bool]]] = Field(
        serialization_alias="icmpRedirectDisable",
        validation_alias="icmpRedirectDisable",
        default=Default[bool](value=True),
    )
    xconnect: Optional[Union[Global[str], Global[IPv4Address], Variable, Default[None]]] = None
    ip_directed_broadcast: Union[Global[bool], Variable, Default[bool]] = Field(
        serialization_alias="ipDirectedBroadcast",
        validation_alias="ipDirectedBroadcast",
        default=Default[bool](value=False),
    )


class InterfaceEthernetParcel(_ParcelBase):
    type_: Literal["lan/vpn/interface/ethernet"] = Field(default="lan/vpn/interface/ethernet", exclude=True)
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="forbid")

    shutdown: Union[Global[bool], Variable, Default[bool]] = Field(
        default=Default[bool](value=True), validation_alias=AliasPath("data", "shutdown")
    )
    interface_name: Union[Global[str], Variable] = Field(validation_alias=AliasPath("data", "interfaceName"))
    ethernet_description: Optional[Union[Global[str], Variable, Default[None]]] = Field(
        default=Default[None](value=None), validation_alias=AliasPath("data", "description")
    )
    interface_ip_address: Union[InterfaceDynamicIPv4Address, InterfaceStaticIPv4Address] = Field(
        validation_alias=AliasPath("data", "intfIpAddress"), default_factory=InterfaceStaticIPv4Address
    )
    dhcp_helper: Optional[Union[Variable, Global[List[str]], Default[None]]] = Field(
        validation_alias=AliasPath("data", "dhcpHelper"), default=None
    )
    interface_ipv6_address: Optional[Union[InterfaceDynamicIPv6Address, InterfaceStaticIPv6Address]] = Field(
        validation_alias=AliasPath("data", "intfIpV6Address"), default=None
    )
    nat: Union[Global[bool], Default[bool]] = Field(
        validation_alias=AliasPath("data", "nat"), default=Default[bool](value=False)
    )
    nat_attributes_ipv4: Optional[EthernetNatAttributesIpv4] = Field(
        validation_alias=AliasPath("data", "natAttributesIpv4"), default=None
    )
    nat_ipv6: Optional[Union[Global[bool], Default[bool]]] = Field(
        validation_alias=AliasPath("data", "natIpv6"), default=Default[bool](value=False)
    )
    nat_attributes_ipv6: Optional[NatAttributesIPv6] = Field(
        validation_alias=AliasPath("data", "natAttributesIpv6"), default=None
    )
    acl_qos: Optional[AclQos] = Field(validation_alias=AliasPath("data", "aclQos"), default=None)
    vrrp_ipv6: Optional[List[VrrpIPv6]] = Field(validation_alias=AliasPath("data", "vrrpIpv6"), default=None)
    vrrp: Optional[List[VrrpIPv4]] = Field(validation_alias=AliasPath("data", "vrrp"), default=None)
    arp: Optional[List[Arp]] = Field(validation_alias=AliasPath("data", "arp"), default=None)
    trustsec: Optional[Trustsec] = Field(validation_alias=AliasPath("data", "trustsec"), default=None)
    advanced: AdvancedEthernetAttributes = Field(
        validation_alias=AliasPath("data", "advanced"), default_factory=AdvancedEthernetAttributes
    )
    port_channel: Optional[PortChannel] = Field(default=None, validation_alias=AliasPath("data", "portChannel"))
    port_channel_interface: Optional[Union[Global[bool], Default[bool]]] = Field(
        default=None, validation_alias=AliasPath("data", "portChannelInterface")
    )
    port_channel_member_interface: Optional[Union[Global[bool], Default[bool]]] = Field(
        default=None, validation_alias=AliasPath("data", "portChannelMemberInterface")
    )

    def set_dynamic_interface_ip_address(self, dhcp_distance: Union[Global[int], Variable]) -> None:
        self.interface_ip_address = InterfaceDynamicIPv4Address(
            dynamic=DynamicDhcpDistance(dynamic_dhcp_distance=dhcp_distance)
        )

    def set_static_primary_interface_ip_address(
        self,
        ip_address: Union[Global[str], Global[IPv4Address], Variable],
        subnet_mask: Optional[Union[Global[str], Variable]] = None,
    ) -> None:
        if subnet_mask is None:
            primary_ip_address = StaticIPv4Address(ip_address=ip_address)
        else:
            primary_ip_address = StaticIPv4Address(ip_address=ip_address, subnet_mask=subnet_mask)
        self.interface_ip_address = InterfaceStaticIPv4Address(
            static=StaticIPv4AddressConfig(primary_ip_address=primary_ip_address)
        )

    def add_static_secondary_interface_ip_address(
        self, ip_address: Union[Global[str], Global[IPv4Address], Variable], subnet_mask: Union[Global[str], Variable]
    ) -> None:
        if self.interface_ip_address is None:
            raise ValueError("Missing static primary IP Address")
        if isinstance(self.interface_ip_address, InterfaceDynamicIPv4Address):
            raise ValueError("Interface IP Address is already dynamic")

        secondary_ip_address = StaticIPv4Address(ip_address=ip_address, subnet_mask=subnet_mask)
        if self.interface_ip_address.static.secondary_ip_address is None:
            self.interface_ip_address.static.secondary_ip_address = []
        self.interface_ip_address.static.secondary_ip_address.append(secondary_ip_address)
