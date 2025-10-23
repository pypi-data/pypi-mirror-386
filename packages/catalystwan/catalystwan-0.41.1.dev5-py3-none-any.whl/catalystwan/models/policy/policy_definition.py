# Copyright 2023 Cisco Systems, Inc. and its affiliates

import datetime
from dataclasses import dataclass, field
from functools import wraps
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, Dict, List, MutableSequence, Optional, Sequence, Set, Tuple, Union, overload
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, RootModel, field_validator, model_validator
from typing_extensions import Annotated, Literal

from catalystwan.models.common import (
    AcceptDropActionType,
    AcceptRejectActionType,
    CarrierType,
    ControlPathType,
    DestinationRegion,
    DNSEntryType,
    DNSTypeEntryType,
    EncapType,
    IcmpMsgType,
    IntStr,
    LossProtectionType,
    MultiRegionRole,
    OriginProtocol,
    SequenceIpType,
    ServiceChainNumber,
    ServiceType,
    SpaceSeparatedInterfaceStr,
    SpaceSeparatedIPv4,
    SpaceSeparatedIPv6,
    SpaceSeparatedNonNegativeIntList,
    SpaceSeparatedServiceAreaList,
    SpaceSeparatedTLOCColorStr,
    SpaceSeparatedUUIDList,
    TLOCActionType,
    TLOCColor,
    TrafficCategory,
    TrafficTargetType,
    check_fields_exclusive,
    str_as_str_list,
)
from catalystwan.models.misc.application_protocols import ApplicationProtocol


def port_set_and_ranges_to_str(ports: Set[int] = set(), port_ranges: List[Tuple[int, int]] = []) -> str:
    assert ports or port_ranges
    ports_str = " ".join(f"{port_begin}-{port_end}" for port_begin, port_end in port_ranges)
    ports_str += " " if ports_str else ""
    ports_str += " ".join(str(p) for p in ports)
    return ports_str


def networks_to_str(networks: Sequence[Union[IPv4Network, IPv6Network]]) -> str:
    return " ".join(str(net) for net in networks)


PLPEntryType = Literal[
    "low",
    "high",
]


PathType = Literal[
    "hierarchical-path",
    "direct-path",
    "transport-gateway-path",
]


SequenceType = Literal[
    "applicationFirewall",
    "data",
    "serviceChaining",
    "trafficEngineering",
    "qos",
    "zoneBasedFW",
    "tloc",
    "route",
    "acl",
    "aclv6",
    "deviceaccesspolicy",
    "deviceaccesspolicyv6",
    "sslDecryption",
    "vedgeRoute",
    "vedgeroute",
    "appRoute",
]


Optimized = Literal[
    "true",
    "false",
]

AdvancedCommunityMatchFlag = Literal["or", "and", "exact"]

MetricType = Literal["type1", "type2"]

SlaNotMetAction = Literal["strict", "fallbackToBestPath"]

VoicePortType = Literal[
    "potsDialPeer",
    "sipDialPeer",
    "srstPhone",
    "voicePort",
]


class Reference(BaseModel):
    ref: UUID


class ReferenceWithId(BaseModel):
    field: Literal["id"] = "id"
    ref: UUID


class ReferenceList(BaseModel):
    ref: SpaceSeparatedUUIDList


class VariableName(BaseModel):
    vip_variable_name: str = Field(serialization_alias="vipVariableName", validation_alias="vipVariableName")


class CommonStation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    number: str


class MediaProfileRef(BaseModel):
    name: int
    ref: UUID


class LineParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    gain: IntStr
    attenuation: IntStr
    echo_cancellor: bool = Field(validation_alias="echoCancellor", serialization_alias="echoCancellor")
    vad: bool
    compand_type: str = Field(serialization_alias="compandType", validation_alias="compandType")
    cptone: str
    impedance: Optional[str] = Field(default=None)


class DidTimers(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    answer_winkwidth: IntStr = Field(
        ge=110, le=290, serialization_alias="answerWinkwidth", validation_alias="answerWinkwidth"
    )
    clear_wait: IntStr = Field(ge=200, le=2000, serialization_alias="clearWait", validation_alias="clearWait")
    wait_wink: IntStr = Field(ge=100, le=6500, serialization_alias="waitWink", validation_alias="waitWink")
    wink_duration: IntStr = Field(ge=50, le=3000, serialization_alias="winkDuration", validation_alias="winkDuration")
    dial_pulse_min_delay: IntStr = Field(
        ge=0, le=5000, serialization_alias="dialPulseMinDelay", validation_alias="dialPulseMinDelay"
    )


class FxoTuningParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    pre_dial_delay: int = Field(ge=0, serialization_alias="preDialDelay", validation_alias="preDialDelay")
    timing_sup_disc: IntStr = Field(serialization_alias="timingSupDisc", validation_alias="timingSupDisc")
    supervisory_disconnect: str = Field(
        serialization_alias="supervisoryDisconnect", validation_alias="supervisoryDisconnect"
    )
    dial_type: str = Field(serialization_alias="dialType", validation_alias="dialType")
    timing_hookflash_out: IntStr = Field(
        serialization_alias="timingHookflashOut", validation_alias="timingHookflashOut"
    )
    timing_guard_out: IntStr = Field(serialization_alias="timingGuardOut", validation_alias="timingGuardOut")
    battery_reversal_det_delay: Optional[IntStr] = Field(
        default=None, serialization_alias="batteryReversalDetDelay", validation_alias="batteryReversalDetDelay"
    )


class FxsTuningParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    timing_hookflash_in_min: IntStr = Field(
        ge=0, le=400, serialization_alias="timingHookflashInMin", validation_alias="timingHookflashInMin"
    )
    timing_hookflash_in_max: IntStr = Field(
        ge=50, le=1500, serialization_alias="timingHookflashInMax", validation_alias="timingHookflashInMax"
    )
    loop_length: str = Field(serialization_alias="loopLength", validation_alias="loopLength")
    ring_frequency: IntStr = Field(serialization_alias="ringFrequency", validation_alias="ringFrequency")
    ring_dc_offset: Optional[str] = Field(
        default=None, serialization_alias="ringDcOffset", validation_alias="ringDcOffset"
    )
    pulse_digit_detection: bool = Field(
        serialization_alias="pulseDigitDetection", validation_alias="pulseDigitDetection"
    )
    ren: IntStr = Field(ge=1, le=5)


class TrunkGroupPreference(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ref: UUID
    preference: int


class TranslationRuleEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ref: UUID
    name: str


class TranslationProfileEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ref: UUID
    name: str
    calling_translation_rule: Optional[TranslationRuleEntry] = Field(
        default=None, serialization_alias="callingTranslationRule", validation_alias="callingTranslationRule"
    )
    called_translation_rule: Optional[TranslationRuleEntry] = Field(
        default=None, serialization_alias="calledTranslationRule", validation_alias="calledTranslationRule"
    )


class SupervisoryDisconnectEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ref: UUID
    name: str


class LocalTLOCListEntryValue(BaseModel):
    color: SpaceSeparatedTLOCColorStr
    encap: Optional[EncapType] = None
    restrict: Optional[str] = None


class TLOCEntryValue(BaseModel):
    ip: IPv4Address
    color: TLOCColor
    encap: EncapType


class ServiceChainEntryValue(BaseModel):
    type: ServiceChainNumber = Field(default="SC1")
    vpn: str
    restrict: Optional[str] = None
    local: Optional[str] = None
    tloc: Optional[TLOCEntryValue] = None


class PacketLengthEntry(BaseModel):
    field: Literal["packetLength"] = "packetLength"
    value: str = Field(description="0-65536 range or single number")

    @staticmethod
    def from_range(packet_lengths: Tuple[int, int]) -> "PacketLengthEntry":
        if packet_lengths[0] == packet_lengths[1]:
            return PacketLengthEntry(value=str(packet_lengths[0]))
        return PacketLengthEntry(value=f"{packet_lengths[0]}-{packet_lengths[1]}")


class PLPEntry(BaseModel):
    field: Literal["plp"] = "plp"
    value: PLPEntryType


class ProtocolEntry(BaseModel):
    field: Literal["protocol"] = "protocol"
    value: str = Field(description="0-255 single numbers separate by space")
    app: Optional[str] = None

    @staticmethod
    def from_protocol_set(protocols: Set[int]) -> "ProtocolEntry":
        return ProtocolEntry(value=" ".join(str(p) for p in protocols))

    @staticmethod
    def from_application_protocols(app_prots: List[ApplicationProtocol]) -> "ProtocolEntry":
        return ProtocolEntry(
            value=" ".join(p.protocol_as_string_of_numbers() for p in app_prots),
            app=" ".join(p.name for p in app_prots),
        )


class DSCPEntry(BaseModel):
    field: Literal["dscp"] = "dscp"
    value: SpaceSeparatedNonNegativeIntList = Field(description="0-63 single numbers separate by space")


class SourceIPEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: Literal["sourceIp"] = "sourceIp"
    value: Optional[SpaceSeparatedIPv4] = Field(default=None, description="IP network specifiers separate by space")
    vip_variable_name: Optional[str] = Field(
        default=None, serialization_alias="vipVariableName", validation_alias="vipVariableName"
    )

    @staticmethod
    def from_ipv4_networks(networks: List[IPv4Network]) -> "SourceIPEntry":
        return SourceIPEntry(value=[IPv4Interface(ip) for ip in networks])

    def as_ipv4_networks(self) -> List[IPv4Network]:
        return [] if not self.value else [IPv4Network(val) for val in self.value]


class SourceIPv6Entry(BaseModel):
    field: Literal["sourceIpv6"] = "sourceIpv6"
    value: SpaceSeparatedIPv6

    @staticmethod
    def from_ipv6_networks(networks: List[IPv6Network]) -> "SourceIPv6Entry":
        return SourceIPv6Entry(value=[IPv6Interface(ip) for ip in networks])

    def as_ipv6_networks(self) -> List[IPv6Network]:
        return [] if not self.value else [IPv6Network(val) for val in self.value]


class IPAddressEntry(BaseModel):
    field: Literal["ipAddress"] = "ipAddress"
    value: IPv4Address


class SourcePortEntry(BaseModel):
    field: Literal["sourcePort"] = "sourcePort"
    value: str = Field(description="0-65535 range or separate by space")

    @staticmethod
    def from_port_set_and_ranges(ports: Set[int] = set(), port_ranges: List[Tuple[int, int]] = []) -> "SourcePortEntry":
        return SourcePortEntry(value=port_set_and_ranges_to_str(ports, port_ranges))


class DestinationIPEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: Literal["destinationIp"] = "destinationIp"
    value: Optional[SpaceSeparatedIPv4] = Field(default=None)
    vip_variable_name: Optional[str] = Field(
        default=None, serialization_alias="vipVariableName", validation_alias="vipVariableName"
    )

    @staticmethod
    def from_ipv4_networks(networks: List[IPv4Network]) -> "DestinationIPEntry":
        return DestinationIPEntry(value=[IPv4Interface(ip) for ip in networks])

    def as_ipv4_networks(self) -> List[IPv4Network]:
        return [] if not self.value else [IPv4Network(val) for val in self.value]


class DestinationIPv6Entry(BaseModel):
    field: Literal["destinationIpv6"] = "destinationIpv6"
    value: SpaceSeparatedIPv6

    @staticmethod
    def from_ipv6_networks(networks: List[IPv6Network]) -> "DestinationIPv6Entry":
        return DestinationIPv6Entry(value=[IPv6Interface(ip) for ip in networks])

    def as_ipv6_networks(self) -> List[IPv6Network]:
        return [] if not self.value else [IPv6Network(val) for val in self.value]


class DestinationPortEntry(BaseModel):
    field: Literal["destinationPort"] = "destinationPort"
    value: str = Field(description="0-65535 range or separate by space")
    app: Optional[str] = None

    @staticmethod
    def from_port_set_and_ranges(
        ports: Set[int] = set(), port_ranges: List[Tuple[int, int]] = []
    ) -> "DestinationPortEntry":
        return DestinationPortEntry(value=port_set_and_ranges_to_str(ports, port_ranges))

    @staticmethod
    def from_application_protocols(app_prots: List[ApplicationProtocol]) -> "DestinationPortEntry":
        return DestinationPortEntry(
            value=" ".join(p.port for p in app_prots if p.port),
            app=" ".join(p.name for p in app_prots),
        )


class TCPEntry(BaseModel):
    field: Literal["tcp"] = "tcp"
    value: Literal["syn"] = "syn"


class DNSEntry(BaseModel):
    field: Literal["dns"] = "dns"
    value: DNSEntryType


class TrafficToEntry(BaseModel):
    field: Literal["trafficTo"] = "trafficTo"
    value: TrafficTargetType


class DestinationRegionEntry(BaseModel):
    field: Literal["destinationRegion"] = "destinationRegion"
    value: DestinationRegion


class AddressEntry(BaseModel):
    field: Literal["address"] = "address"
    ref: UUID


class AsPathListMatchEntry(BaseModel):
    field: Literal["asPath"] = "asPath"
    ref: UUID


class AsPathActionEntryValue(BaseModel):
    prepend: Optional[SpaceSeparatedNonNegativeIntList] = None
    exclude: Optional[SpaceSeparatedNonNegativeIntList] = None


class AsPathActionEntry(BaseModel):
    field: Literal["asPath"] = "asPath"
    value: AsPathActionEntryValue


class SourceFQDNEntry(BaseModel):
    field: Literal["sourceFqdn"] = "sourceFqdn"
    value: str = Field(max_length=120)


class DestinationFQDNEntry(BaseModel):
    field: Literal["destinationFqdn"] = "destinationFqdn"
    value: str = Field(max_length=120)


class SourceGeoLocationEntry(BaseModel):
    field: Literal["sourceGeoLocation"] = "sourceGeoLocation"
    value: str = Field(description="Space separated list of ISO3166 country codes")


class DestinationGeoLocationEntry(BaseModel):
    field: Literal["destinationGeoLocation"] = "destinationGeoLocation"
    value: str = Field(description="Space separated list of ISO3166 country codes")


class ProtocolNameEntry(BaseModel):
    field: Literal["protocolName"] = "protocolName"
    value: str

    @staticmethod
    def from_application_protocols(app_prots: List[ApplicationProtocol]) -> "ProtocolNameEntry":
        return ProtocolNameEntry(value=" ".join(p.name for p in app_prots))


class ForwardingClassEntry(BaseModel):
    field: Literal["forwardingClass"] = "forwardingClass"
    value: str = Field(max_length=32)


class NATPoolEntry(BaseModel):
    field: Literal["pool"] = "pool"
    value: str


class UseVPNEntry(BaseModel):
    field: Literal["useVpn"] = "useVpn"
    value: str = "0"


class FallBackEntry(BaseModel):
    field: Literal["fallback"] = "fallback"
    value: Literal["", "true"]

    @property
    def as_bool(self) -> bool:
        return True if self.value == "true" else False


class DiaPoolEntry(BaseModel):
    field: Literal["diaPool"] = "diaPool"
    value: SpaceSeparatedNonNegativeIntList


class DiaInterfaceEntry(BaseModel):
    field: Literal["diaInterface"] = "diaInterface"
    value: SpaceSeparatedInterfaceStr


class BypassEntry(BaseModel):
    field: Literal["bypass"] = "bypass"
    value: Literal["", "true"]

    @property
    def as_bool(self) -> bool:
        return True if self.value == "true" else False


class NextHopActionEntry(BaseModel):
    field: Literal["nextHop"] = "nextHop"
    value: Union[IPv4Address, IPv6Address]


class NextHopIpv6ActionEntry(BaseModel):
    field: Literal["nextHopIpv6"] = "nextHopIpv6"
    value: IPv6Address


class NextHopMatchEntry(BaseModel):
    field: Literal["nextHop"] = "nextHop"
    ref: UUID


class NextHopLooseEntry(BaseModel):
    field: Literal["nextHopLoose"] = "nextHopLoose"
    value: Annotated[bool, PlainSerializer(lambda x: str(x).lower(), return_type=str, when_used="json-unless-none")]


class OMPTagEntry(BaseModel):
    field: Literal["ompTag"] = "ompTag"
    value: IntStr = Field(description="Number in range 0-4294967295", ge=0, le=4294967295)


class OriginEntry(BaseModel):
    field: Literal["origin"] = "origin"
    value: OriginProtocol


class OriginatorEntry(BaseModel):
    field: Literal["originator"] = "originator"
    value: IPv4Address


class PreferenceEntry(BaseModel):
    field: Literal["preference"] = "preference"
    value: str = Field(description="Number in range 0-4294967295")


class PathTypeEntry(BaseModel):
    field: Literal["pathType"] = "pathType"
    value: ControlPathType


class RegionEntry(BaseModel):
    field: Literal["regionId"] = "regionId"
    value: str


class RoleEntry(BaseModel):
    field: Literal["role"] = "role"
    value: MultiRegionRole


class SiteEntry(BaseModel):
    field: Literal["siteId"] = "siteId"
    value: str = Field(description="Site ID numeric value")


class LocalTLOCListEntry(BaseModel):
    field: Literal["localTlocList"] = "localTlocList"
    value: LocalTLOCListEntryValue


class DNSTypeEntry(BaseModel):
    field: Literal["dnsType"] = "dnsType"
    value: DNSTypeEntryType


class ServiceChainEntry(BaseModel):
    field: Literal["serviceChain"] = "serviceChain"
    value: ServiceChainEntryValue


class VPNEntry(BaseModel):
    field: Literal["vpn"] = "vpn"
    value: str


class TLOCEntry(BaseModel):
    field: Literal["tloc"] = "tloc"
    value: TLOCEntryValue


class CommunityEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    field: Literal["community"] = "community"
    value: Optional[str] = Field(
        default=None, description="Example: 1000:10000 or internet or local-AS or no advertise or no-export"
    )
    vip_variable_name: Optional[str] = Field(
        default=None,
        serialization_alias="vipVariableName",
        validation_alias="vipVariableName",
        description="Example: 1000:10000 or internet or local-AS or no advertise or no-export",
    )


class CommunityAdditiveEntry(BaseModel):
    field: Literal["communityAdditive"] = "communityAdditive"
    value: Literal["true"] = "true"


class CarrierEntry(BaseModel):
    field: Literal["carrier"] = "carrier"
    value: CarrierType


class DomainIDEntry(BaseModel):
    field: Literal["domainId"] = "domainId"
    value: str = Field(description="Number in range 1-4294967295")


class GroupIDEntry(BaseModel):
    field: Literal["groupId"] = "groupId"
    value: str = Field(description="Number in range 0-4294967295")


class NextHeaderEntry(BaseModel):
    field: Literal["nextHeader"] = "nextHeader"
    value: str = Field(description="0-63 single numbers separate by space")


class AggregatorActionEntryValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    aggregator: IntStr = Field(description="Number in range 1-4294967295", ge=0, le=4294967295)
    ip_address: Union[IPv4Address, IPv6Address] = Field(serialization_alias="ipAddress", validation_alias="ipAddress")


class AggregatorActionEntry(BaseModel):
    field: Literal["aggregator"] = "aggregator"
    value: AggregatorActionEntryValue


class TrafficClassEntry(BaseModel):
    field: Literal["trafficClass"] = "trafficClass"
    value: str = Field(description="Number in range 0-63")


class LocalPreferenceEntry(BaseModel):
    field: Literal["localPreference"] = "localPreference"
    value: IntStr = Field(ge=0, le=4294967295, description="Number in range 0-4294967295")


class MetricEntry(BaseModel):
    field: Literal["metric"] = "metric"
    value: IntStr = Field(ge=0, le=4294967295, description="Number in range 0-4294967295")


class MetricTypeEntry(BaseModel):
    field: Literal["metricType"] = "metricType"
    value: MetricType


class OspfTagEntry(BaseModel):
    field: Literal["ospfTag"] = "ospfTag"
    value: IntStr = Field(ge=0, le=4294967295, description="Number in range 0-4294967295")


class PeerEntry(BaseModel):
    field: Literal["peer"] = "peer"
    value: Union[IPv4Address, IPv6Address]


class AtomicAggregateActionEntry(BaseModel):
    field: Literal["atomicAggregate"] = "atomicAggregate"
    value: Literal["true"] = "true"


class WeightEntry(BaseModel):
    field: Literal["weight"] = "weight"
    value: IntStr = Field(ge=0, le=4294967295, description="Number in range 0-4294967295")


class AdvancedCommunityEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: Literal["advancedCommunity"] = "advancedCommunity"

    match_flag: AdvancedCommunityMatchFlag = Field(
        default="or",
        serialization_alias="matchFlag",
        validation_alias="matchFlag",
        description="The 'and' and 'exact' conditions are applicable to only one community list",
    )

    refs: List[UUID] = []


class ExpandedCommunityInLineEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: Literal["expandedCommunityInline"] = "expandedCommunityInline"
    vip_variable_name: str = Field(serialization_alias="vipVariableName", validation_alias="vipVariableName")


class ExtendedCommunityEntry(BaseModel):
    field: Literal["extCommunity"] = "extCommunity"
    ref: UUID


NATVPNEntries = Annotated[
    Union[
        BypassEntry,
        DiaPoolEntry,
        DiaInterfaceEntry,
        FallBackEntry,
        UseVPNEntry,
    ],
    Field(discriminator="field"),
]


@dataclass
class NATVPNParams:
    bypass: bool = False
    dia_pool: List[int] = field(default_factory=list)
    dia_interface: List[str] = field(default_factory=list)
    fallback: bool = False
    vpn: Optional[int] = None

    def as_entry_list(self) -> List[NATVPNEntries]:
        entries: List[NATVPNEntries] = []
        if self.bypass:
            entries.append(BypassEntry(value="true"))
        if self.dia_pool:
            entries.append(DiaPoolEntry(value=self.dia_pool))
        if self.dia_interface:
            entries.append(DiaInterfaceEntry(value=self.dia_interface))
        if self.fallback:
            entries.append(FallBackEntry(value="true"))
        if self.vpn is not None:
            entries.append(UseVPNEntry(value=str(self.vpn)))
        return entries


class NATVPNEntry(RootModel):
    root: List[NATVPNEntries]

    @staticmethod
    def from_params(params: NATVPNParams) -> "NATVPNEntry":
        return NATVPNEntry(root=params.as_entry_list())

    def get_params(self) -> NATVPNParams:
        params = NATVPNParams()
        for param in self.root:
            if param.field == "bypass":
                params.bypass = param.as_bool
            elif param.field == "diaInterface":
                params.dia_interface = param.value
            elif param.field == "diaPool":
                params.dia_pool = param.value
            elif param.field == "fallback":
                params.fallback = param.as_bool
            elif param.field == "useVpn":
                params.vpn = int(param.value)
        return params


class ICMPMessageEntry(BaseModel):
    field: Literal["icmpMessage"] = "icmpMessage"
    value: List[IcmpMsgType]

    _value = field_validator("value", mode="before")(str_as_str_list)


class SourceDataPrefixListEntry(BaseModel):
    field: Literal["sourceDataPrefixList"] = "sourceDataPrefixList"
    ref: SpaceSeparatedUUIDList = Field(
        description="usually single id but zone based firewall can use multiple ids separated by space"
    )


class SourceDataIPv6PrefixListEntry(BaseModel):
    field: Literal["sourceDataIpv6PrefixList"] = "sourceDataIpv6PrefixList"
    ref: SpaceSeparatedUUIDList = Field(
        description="usually single id but zone based firewall can use multiple ids separated by space"
    )


class DestinationDataPrefixListEntry(BaseModel):
    field: Literal["destinationDataPrefixList"] = "destinationDataPrefixList"
    ref: SpaceSeparatedUUIDList = Field(
        description="usually single id but zone based firewall can use multiple ids separated by space"
    )


class DestinationDataIPv6PrefixListEntry(BaseModel):
    field: Literal["destinationDataIpv6PrefixList"] = "destinationDataIpv6PrefixList"
    ref: SpaceSeparatedUUIDList = Field(
        description="usually single id but zone based firewall can use multiple ids separated by space"
    )


class DNSAppListEntry(BaseModel):
    field: Literal["dnsAppList"] = "dnsAppList"
    ref: UUID


class AppListEntry(BaseModel):
    field: Literal["appList"] = "appList"
    ref: SpaceSeparatedUUIDList


class SaaSAppListEntry(BaseModel):
    field: Literal["saasAppList"] = "saasAppList"
    ref: UUID


class AppListFlatEntry(BaseModel):
    field: Literal["appListFlat"] = "appListFlat"
    ref: SpaceSeparatedUUIDList


class SourceFQDNListEntry(BaseModel):
    field: Literal["sourceFqdnList"] = "sourceFqdnList"
    ref: UUID


class DestinationFQDNListEntry(BaseModel):
    field: Literal["destinationFqdnList"] = "destinationFqdnList"
    ref: SpaceSeparatedUUIDList


class SourceGeoLocationListEntry(BaseModel):
    field: Literal["sourceGeoLocationList"] = "sourceGeoLocationList"
    ref: SpaceSeparatedUUIDList


class DestinationGeoLocationListEntry(BaseModel):
    field: Literal["destinationGeoLocationList"] = "destinationGeoLocationList"
    ref: SpaceSeparatedUUIDList


class ProtocolNameListEntry(BaseModel):
    field: Literal["protocolNameList"] = "protocolNameList"
    ref: SpaceSeparatedUUIDList


class SourcePortListEntry(BaseModel):
    field: Literal["sourcePortList"] = "sourcePortList"
    ref: SpaceSeparatedUUIDList


class SourceScalableGroupTagListEntry(BaseModel):
    field: Literal["sourceScalableGroupTagList"] = "sourceScalableGroupTagList"
    ref: SpaceSeparatedUUIDList


class SourceSecurityGroupEntry(BaseModel):
    field: Literal["sourceSecurityGroup"] = "sourceSecurityGroup"
    ref: SpaceSeparatedUUIDList


class DestinationPortListEntry(BaseModel):
    field: Literal["destinationPortList"] = "destinationPortList"
    ref: SpaceSeparatedUUIDList = Field(
        description="usually single id but zone based firewall can use multiple ids separated by space"
    )


class DestinationScalableGroupTagListEntry(BaseModel):
    field: Literal["destinationScalableGroupTagList"] = "destinationScalableGroupTagList"
    ref: SpaceSeparatedUUIDList


class DestinationSecurityGroupEntry(BaseModel):
    field: Literal["destinationSecurityGroup"] = "destinationSecurityGroup"
    ref: SpaceSeparatedUUIDList


class RuleSetListEntry(BaseModel):
    field: Literal["ruleSetList"] = "ruleSetList"
    ref: SpaceSeparatedUUIDList


class PolicerListEntry(BaseModel):
    field: Literal["policer"] = "policer"
    ref: UUID


class TLOCListEntry(BaseModel):
    field: Literal["tlocList"] = "tlocList"
    ref: UUID


class SourceVpnEntry(BaseModel):
    field: Literal["sourceVpn"] = "sourceVpn"
    value: str = Field(description="VPN ids numbers separated by space")


class DestinationVpnEntry(BaseModel):
    field: Literal["destinationVpn"] = "destinationVpn"
    value: str = Field(description="VPN ids numbers separated by space")


class PrefferedColorGroupListEntry(BaseModel):
    field: Literal["preferredColorGroup"] = "preferredColorGroup"
    ref: UUID
    color_restrict: bool = Field(False, serialization_alias="colorRestrict", validation_alias="colorRestrict")
    model_config = ConfigDict(populate_by_name=True)


class ColorListEntry(BaseModel):
    field: Literal["colorList"] = "colorList"
    ref: UUID


class CommunityListEntry(BaseModel):
    field: Literal["community"] = "community"
    ref: UUID


class ExpandedCommunityListEntry(BaseModel):
    field: Literal["expandedCommunity"] = "expandedCommunity"
    ref: UUID


class SiteListEntry(BaseModel):
    field: Literal["siteList"] = "siteList"
    ref: UUID


class VPNListEntry(BaseModel):
    field: Literal["vpnList"] = "vpnList"
    ref: UUID


class PrefixListEntry(BaseModel):
    field: Literal["prefixList"] = "prefixList"
    ref: UUID


class Ipv6PrefixListEntry(BaseModel):
    field: Literal["ipv6prefixList"] = "ipv6prefixList"
    ref: UUID


class RegionListEntry(BaseModel):
    field: Literal["regionList"] = "regionList"
    ref: UUID


class ClassMapListEntry(BaseModel):
    field: Literal["class"] = "class"
    ref: UUID


class ServiceEntryValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: ServiceType
    vpn: Optional[IntStr] = None
    tloc: Optional[TLOCEntryValue] = None
    tloc_list: Optional[TLOCListEntry] = Field(
        default=None, validation_alias="tlocList", serialization_alias="tlocList"
    )
    restrict: Optional[str] = None
    local: Optional[str] = None

    @model_validator(mode="after")
    def tloc_xor_tloc_list(self):
        check_fields_exclusive(self.__dict__, {"tloc", "tloc_list"}, False)
        return self


class ServiceEntry(BaseModel):
    field: Literal["service"] = "service"
    value: ServiceEntryValue


class TLOCActionEntry(BaseModel):
    field: Literal["tlocAction"] = "tlocAction"
    value: TLOCActionType


class AffinityEntry(BaseModel):
    field: Literal["affinity"] = "affinity"
    value: str = Field(description="Number in range 0-63")


RedirectDNSActionEntry = Union[IPAddressEntry, DNSTypeEntry]


class ServiceAreaEntry(BaseModel):
    field: Literal["serviceArea"] = "serviceArea"
    value: SpaceSeparatedServiceAreaList


class TrafficCategoryEntry(BaseModel):
    field: Literal["trafficCategory"] = "trafficCategory"
    value: TrafficCategory


class LogAction(BaseModel):
    type: Literal["log"] = "log"
    parameter: str = ""


class CountAction(BaseModel):
    type: Literal["count"] = "count"
    parameter: str


class NATAction(BaseModel):
    type: Literal["nat"] = "nat"
    parameter: Union[NATPoolEntry, NATVPNEntry]

    @staticmethod
    def from_nat_pool(nat_pool: int) -> "NATAction":
        return NATAction(parameter=NATPoolEntry(value=str(nat_pool)))

    @staticmethod
    def from_nat_vpn(
        use_vpn: int = 0,
        *,
        fallback: bool = False,
        bypass: bool = False,
        dia_pool: List[int] = [],
        dia_interface: List[str] = [],
    ) -> "NATAction":
        params = NATVPNParams(
            bypass=bypass,
            dia_pool=dia_pool,
            dia_interface=dia_interface,
            fallback=fallback,
            vpn=use_vpn,
        )
        return NATAction(parameter=NATVPNEntry.from_params(params))

    @property
    def nat_pool(self) -> Optional[int]:
        if isinstance(self.parameter, NATPoolEntry):
            return int(self.parameter.value)
        return None

    @property
    def nat_vpn(self) -> Optional[NATVPNParams]:
        if isinstance(self.parameter, NATVPNEntry):
            return self.parameter.get_params()
        return None


class CFlowDAction(BaseModel):
    type: Literal["cflowd"] = "cflowd"


class RedirectDNSAction(BaseModel):
    type: Literal["redirectDns"] = "redirectDns"
    parameter: RedirectDNSActionEntry

    @staticmethod
    def from_ip_address(ip: IPv4Address) -> "RedirectDNSAction":
        return RedirectDNSAction(parameter=IPAddressEntry(value=ip))

    @staticmethod
    def from_dns_type(dns_type: DNSTypeEntryType = "host") -> "RedirectDNSAction":
        return RedirectDNSAction(parameter=DNSTypeEntry(value=dns_type))

    def get_ip(self) -> Optional[IPv4Address]:
        if self.parameter.field == "ipAddress":
            return self.parameter.value
        return None

    def get_dns_type(self) -> Optional[DNSTypeEntryType]:
        if self.parameter.field == "dnsType":
            return self.parameter.value
        return None


class TCPOptimizationAction(BaseModel):
    type: Literal["tcpOptimization"] = "tcpOptimization"
    parameter: str = ""


class DREOptimizationAction(BaseModel):
    type: Literal["dreOptimization"] = "dreOptimization"
    parameter: str = ""


class ServiceNodeGroupAction(BaseModel):
    type: Literal["serviceNodeGroup"] = "serviceNodeGroup"
    parameter: str = Field(default="", pattern=r"^(SNG-APPQOE(3[01]|[12][0-9]|[1-9])?)?$")


class LossProtectionAction(BaseModel):
    type: Literal["lossProtect"] = "lossProtect"
    parameter: LossProtectionType


class LossProtectionFECAction(BaseModel):
    type: Literal["lossProtectFec"] = "lossProtectFec"
    parameter: LossProtectionType = "fecAlways"
    value: Optional[str] = Field(default=None, description="BETA number in range 1-5")


class LossProtectionPacketDuplicationAction(BaseModel):
    type: Literal["lossProtectPktDup"] = "lossProtectPktDup"
    parameter: LossProtectionType = "packetDuplication"


class SecureInternetGatewayAction(BaseModel):
    type: Literal["sig"] = "sig"
    parameter: str = ""


class FallBackToRoutingAction(BaseModel):
    type: Literal["fallbackToRouting"] = "fallbackToRouting"
    parameter: str = ""


class ExportToAction(BaseModel):
    type: Literal["exportTo"] = "exportTo"
    parameter: VPNListEntry


class MirrorAction(BaseModel):
    type: Literal["mirror"] = "mirror"
    parameter: Reference


class ClassMapAction(BaseModel):
    type: Literal["class"] = "class"
    parameter: Reference


class PolicerAction(BaseModel):
    type: Literal["policer"] = "policer"
    parameter: Reference


class ConnectionEventsAction(BaseModel):
    type: Literal["connectionEvents"] = "connectionEvents"
    parameter: str = ""


class AdvancedInspectionProfileAction(BaseModel):
    type: Literal["advancedInspectionProfile"] = "advancedInspectionProfile"
    parameter: ReferenceWithId


class BackupSlaPrefferedColorAction(BaseModel):
    type: Literal["backupSlaPreferredColor"] = "backupSlaPreferredColor"
    parameter: SpaceSeparatedTLOCColorStr


class SlaName(BaseModel):
    field: Literal["name"] = "name"
    ref: UUID


class SlaPreferredColor(BaseModel):
    field: Literal["preferredColor"] = "preferredColor"
    value: SpaceSeparatedTLOCColorStr


class SlaPreferredRemoteColor(BaseModel):
    field: Literal["preferredRemoteColor"] = "preferredRemoteColor"
    value: TLOCColor
    remote_color_restrict: Optional[bool] = Field(
        default=None, serialization_alias="remoteColorRestrict", validation_alias="remoteColorRestrict"
    )


class SlaPreferredColorGroup(BaseModel):
    field: Literal["preferredColorGroup"] = "preferredColorGroup"
    ref: UUID


class SlaNotMet(BaseModel):
    field: SlaNotMetAction


SlaClassActionParam = Annotated[
    Union[
        SlaName,
        SlaPreferredColor,
        SlaPreferredColorGroup,
        SlaPreferredRemoteColor,
        SlaNotMet,
    ],
    Field(discriminator="field"),
]


class SlaClassAction(BaseModel):
    type: Literal["slaClass"] = "slaClass"
    parameter: List[SlaClassActionParam] = Field(default_factory=list)

    @overload
    @staticmethod
    def from_params(
        sla_class: UUID, not_met_action: Optional[SlaNotMetAction] = None, *, preferred_color: List[TLOCColor]
    ) -> "SlaClassAction": ...

    @overload
    @staticmethod
    def from_params(
        sla_class: UUID, not_met_action: Optional[SlaNotMetAction] = None, *, preferred_color_group: UUID
    ) -> "SlaClassAction": ...

    @staticmethod
    def from_params(
        sla_class: UUID,
        not_met_action: Optional[SlaNotMetAction] = None,
        *,
        preferred_color: Optional[List[TLOCColor]] = None,
        preferred_color_group: Optional[UUID] = None,
    ) -> "SlaClassAction":
        action = SlaClassAction()
        action.parameter.append(SlaName(ref=sla_class))
        if not_met_action:
            action.parameter.append(SlaNotMet(field=not_met_action))
        if preferred_color:
            action.parameter.append(SlaPreferredColor(value=preferred_color))
        if preferred_color_group:
            action.parameter.append(SlaPreferredColorGroup(ref=preferred_color_group))
        return action


class CloudSaaSAction(BaseModel):
    type: Literal["cloudSaas"] = "cloudSaas"
    parameter: str = Field(default="")


ActionSetEntry = Annotated[
    Union[
        AffinityEntry,
        AggregatorActionEntry,
        AsPathActionEntry,
        AtomicAggregateActionEntry,
        CommunityAdditiveEntry,
        CommunityEntry,
        DSCPEntry,
        ForwardingClassEntry,
        LocalPreferenceEntry,
        LocalTLOCListEntry,
        MetricEntry,
        MetricTypeEntry,
        NextHopActionEntry,
        NextHopIpv6ActionEntry,
        NextHopLooseEntry,
        OMPTagEntry,
        OriginatorEntry,
        OriginEntry,
        OspfTagEntry,
        PolicerListEntry,
        PreferenceEntry,
        PrefferedColorGroupListEntry,
        ServiceChainEntry,
        ServiceEntry,
        TLOCActionEntry,
        TLOCEntry,
        TLOCListEntry,
        TrafficClassEntry,
        VPNEntry,
        WeightEntry,
    ],
    Field(discriminator="field"),
]


class ActionSet(BaseModel):
    type: Literal["set"] = "set"
    parameter: List[ActionSetEntry] = Field(default_factory=list)


ActionEntry = Annotated[
    Union[
        ActionSet,
        AdvancedInspectionProfileAction,
        BackupSlaPrefferedColorAction,
        CFlowDAction,
        ClassMapAction,
        CloudSaaSAction,
        ConnectionEventsAction,
        CountAction,
        DREOptimizationAction,
        ExportToAction,
        FallBackToRoutingAction,
        LogAction,
        LossProtectionAction,
        LossProtectionFECAction,
        LossProtectionPacketDuplicationAction,
        MirrorAction,
        NATAction,
        PolicerAction,
        RedirectDNSAction,
        SecureInternetGatewayAction,
        ServiceNodeGroupAction,
        SlaClassAction,
        TCPOptimizationAction,
    ],
    Field(discriminator="type"),
]

MatchEntry = Annotated[
    Union[
        AddressEntry,
        AdvancedCommunityEntry,
        AppListEntry,
        AppListFlatEntry,
        AsPathListMatchEntry,
        CarrierEntry,
        ClassMapListEntry,
        ColorListEntry,
        CommunityListEntry,
        DestinationDataIPv6PrefixListEntry,
        DestinationDataPrefixListEntry,
        DestinationFQDNEntry,
        DestinationFQDNListEntry,
        DestinationGeoLocationEntry,
        DestinationGeoLocationListEntry,
        DestinationIPEntry,
        DestinationIPv6Entry,
        DestinationPortEntry,
        DestinationPortListEntry,
        DestinationRegionEntry,
        DestinationScalableGroupTagListEntry,
        DestinationSecurityGroupEntry,
        DestinationVpnEntry,
        DNSAppListEntry,
        DNSEntry,
        DomainIDEntry,
        DSCPEntry,
        ExpandedCommunityInLineEntry,
        ExpandedCommunityListEntry,
        ExpandedCommunityListEntry,
        ExtendedCommunityEntry,
        GroupIDEntry,
        ICMPMessageEntry,
        Ipv6PrefixListEntry,
        LocalPreferenceEntry,
        MetricEntry,
        NextHeaderEntry,
        NextHopMatchEntry,
        OMPTagEntry,
        OriginatorEntry,
        OriginEntry,
        OspfTagEntry,
        PacketLengthEntry,
        PathTypeEntry,
        PeerEntry,
        PLPEntry,
        PreferenceEntry,
        PrefixListEntry,
        ProtocolEntry,
        ProtocolNameEntry,
        ProtocolNameListEntry,
        RegionEntry,
        RegionListEntry,
        RoleEntry,
        RuleSetListEntry,
        SaaSAppListEntry,
        ServiceAreaEntry,
        SiteEntry,
        SiteListEntry,
        SiteListEntry,
        SourceDataIPv6PrefixListEntry,
        SourceDataPrefixListEntry,
        SourceFQDNEntry,
        SourceFQDNListEntry,
        SourceGeoLocationEntry,
        SourceGeoLocationListEntry,
        SourceIPEntry,
        SourceIPv6Entry,
        SourcePortEntry,
        SourcePortListEntry,
        SourceScalableGroupTagListEntry,
        SourceSecurityGroupEntry,
        SourceVpnEntry,
        TCPEntry,
        TLOCEntry,
        TLOCListEntry,
        TrafficCategoryEntry,
        TrafficClassEntry,
        TrafficToEntry,
        VPNEntry,
        VPNListEntry,
    ],
    Field(discriminator="field"),
]

MUTUALLY_EXCLUSIVE_FIELDS = [
    {"destinationDataPrefixList", "destinationIp"},
    {"destinationDataIpv6PrefixList", "destinationIpv6"},
    {"sourceDataPrefixList", "sourceIp"},
    {"sourceDataIpv6PrefixList", "sourceIpv6"},
    {"protocolName", "protocolNameList", "protocol", "destinationPort", "destinationPortList"},
    {"localTlocList", "preferredColorGroup"},
    {"sig", "fallbackToRouting", "nat", "nextHop", "serviceChain"},
    {"regionId", "regionList"},
    {"siteId", "siteList"},
    {"tloc", "tlocList"},
    {"service", "tlocAction"},
]


def _generate_field_name_check_lookup(spec: Sequence[Set[str]]) -> Dict[str, List[str]]:
    lookup: Dict[str, List[str]] = {}
    for exclusive_set in spec:
        for fieldname in exclusive_set:
            lookup[fieldname] = list(exclusive_set - {fieldname})
    return lookup


MUTUALLY_EXCLUSIVE_FIELD_LOOKUP = _generate_field_name_check_lookup(MUTUALLY_EXCLUSIVE_FIELDS)


class Match(BaseModel):
    entries: Sequence[MatchEntry]


class Action(BaseModel):
    pass


class PolicyDefinitionSequenceBase(BaseModel):
    sequence_id: int = Field(default=0, serialization_alias="sequenceId", validation_alias="sequenceId")
    sequence_name: Optional[str] = Field(
        default=None, serialization_alias="sequenceName", validation_alias="sequenceName"
    )
    base_action: Optional[str] = Field(default=None, serialization_alias="baseAction", validation_alias="baseAction")
    sequence_type: SequenceType = Field(serialization_alias="sequenceType", validation_alias="sequenceType")
    sequence_ip_type: Optional[SequenceIpType] = Field(
        default="ipv4", serialization_alias="sequenceIpType", validation_alias="sequenceIpType"
    )
    ruleset: Optional[bool] = None
    match: Match
    actions: Optional[Sequence[ActionEntry]] = None

    @staticmethod
    def _check_field_collision(field: str, fields: Sequence[str]) -> None:
        existing_fields = set(fields)
        forbidden_fields = set(MUTUALLY_EXCLUSIVE_FIELD_LOOKUP.get(field, []))
        colliding_fields = set(existing_fields) & set(forbidden_fields)
        assert not colliding_fields, f"{field} is mutually exclusive with {colliding_fields}"

    def _check_match_can_be_inserted(self, match: MatchEntry) -> None:
        self._check_field_collision(
            match.field,
            [entry.field for entry in self.match.entries],
        )

    def _check_action_can_be_inserted_in_set(
        self, action: ActionSetEntry, action_set_param: List[ActionSetEntry]
    ) -> None:
        self._check_field_collision(
            action.field,
            [param.field for param in action_set_param],
        )

    def _get_match_entries_by_field(self, field: str) -> Sequence[MatchEntry]:
        return [entry for entry in self.match.entries if entry.field == field]

    def _remove_match(self, match_type: Any) -> None:
        if isinstance(self.match.entries, MutableSequence):
            self.match.entries[:] = [entry for entry in self.match.entries if entry is not match_type]

    def _insert_match(self, match: MatchEntry, insert_field_check: bool = True) -> int:
        # inserts new item or replaces item with same field name if found
        if insert_field_check:
            self._check_match_can_be_inserted(match)
        if isinstance(self.match.entries, MutableSequence):
            for index, entry in enumerate(self.match.entries):
                if match.field == entry.field:
                    self.match.entries[index] = match
                    return index
            self.match.entries.append(match)
            return len(self.match.entries) - 1
        else:
            raise TypeError("Match entries must be defined as MutableSequence (eg. List) to use _insert_match method")

    def _insert_action(self, action: ActionEntry) -> None:
        if isinstance(self.actions, MutableSequence):
            for index, entry in enumerate(self.actions):
                if action.type == entry.type:
                    self.actions[index] = action
                    return
            self.actions.append(action)
        else:
            raise TypeError("Action entries must be defined as MutableSequence (eg. List) to use _insert_match method")

    def _remove_action(self, action_type_name: str) -> None:
        if isinstance(self.actions, MutableSequence):
            self.actions[:] = [action for action in self.actions if action.type != action_type_name]

    def _insert_action_in_set(self, action: ActionSetEntry) -> None:
        if isinstance(self.actions, MutableSequence):
            # Check if ActionSet entry already exist
            action_sets = [act for act in self.actions if isinstance(act, ActionSet)]
            if len(action_sets) < 1:
                # if not found insert new empty ActionSet
                action_set = ActionSet()
                self.actions.append(action_set)
            else:
                action_set = action_sets[0]
            # Now we operate on action_set parameter list
            self._check_action_can_be_inserted_in_set(action, action_set.parameter)
            for index, param in enumerate(action_set.parameter):
                if action.field == param.field:
                    action_set.parameter[index] = action
                    return
            action_set.parameter.append(action)

    def _remove_action_from_set(self, field_name: str) -> None:
        if isinstance(self.actions, MutableSequence):
            for action in self.actions:
                if isinstance(action, ActionSet):
                    action.parameter[:] = [param for param in action.parameter if param.field != field_name]


def accept_action(method):
    @wraps(method)
    def wrapper(self: PolicyDefinitionSequenceBase, *args, **kwargs):
        assert self.base_action == "accept", f"{method.__name__} only allowed when base_action is accept"
        return method(self, *args, **kwargs)

    return wrapper


class PolicyActionBase(BaseModel):
    type: str


class PolicyAcceptRejectAction(PolicyActionBase):
    type: AcceptRejectActionType


class PolicyAcceptDropAction(PolicyActionBase):
    type: AcceptDropActionType


class InfoTag(BaseModel):
    info_tag: Optional[str] = Field("", serialization_alias="infoTag", validation_alias="infoTag")


class PolicyDefinitionId(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    definition_id: UUID = Field(serialization_alias="definitionId", validation_alias="definitionId")


class PolicyReference(BaseModel):
    id: UUID
    property: str


class DefinitionWithSequencesCommonBase(BaseModel):
    default_action: Optional[PolicyActionBase] = Field(
        default=None,
        serialization_alias="defaultAction",
        validation_alias="defaultAction",
    )
    sequences: Optional[Sequence[PolicyDefinitionSequenceBase]] = None

    def _enumerate_sequences(self, from_index: int = 0) -> None:
        """Updates sequence entries with appropriate index.

        Args:
            from_index (int, optional): Only rules after that index in table will be updated. Defaults to 0.
        """
        if isinstance(self.sequences, MutableSequence):
            start_index = from_index
            sequence_count = len(self.sequences)
            if from_index < 0:
                start_index = sequence_count - start_index
            for i in range(start_index, sequence_count):
                self.sequences[i].sequence_id = i + 1
        else:
            raise TypeError("sequences be defined as MutableSequence (eg. List) to use _enumerate_sequences method")

    def pop(self, index: int = -1) -> None:
        """Removes a sequence item at given index, consecutive sequence items will be enumarated again.

        Args:
            index (int, optional): Defaults to -1.
        """
        if isinstance(self.sequences, MutableSequence):
            self.sequences.pop(index)
            self._enumerate_sequences(index)
        else:
            raise TypeError("sequences be defined as MutableSequence (eg. List) to use pop method")

    def add(self, item: PolicyDefinitionSequenceBase) -> int:
        """Adds new sequence item as last in table, index will be autogenerated.

        Args:
            item (DefinitionSequence): item to be added to sequences

        Returns:
            int: index at which item was added
        """
        if isinstance(self.sequences, MutableSequence):
            insert_index = len(self.sequences)
            self.sequences.append(item)
            self._enumerate_sequences(insert_index)
            return insert_index
        else:
            raise TypeError("sequences be defined as MutableSequence (eg. List) to add method")


class PolicyDefinitionBase(BaseModel):
    name: str = Field(
        pattern="^[a-zA-Z0-9._-]{1,128}$",
        description="Can include only alpha-numeric characters, "
        "dot '.' or hyphen '-' or underscore '_'; maximum 128 characters",
    )
    description: str = "default description"
    type: str
    mode: Optional[str] = None
    optimized: Optional[Optimized] = "false"


class PolicyDefinitionInfo(PolicyDefinitionBase, PolicyDefinitionId):
    last_updated: datetime.datetime = Field(serialization_alias="lastUpdated", validation_alias="lastUpdated")
    owner: str
    reference_count: int = Field(serialization_alias="referenceCount", validation_alias="referenceCount")
    references: List[PolicyReference]


class PolicyDefinitionGetResponse(PolicyDefinitionInfo):
    is_activated_by_vsmart: bool = Field(
        serialization_alias="isActivatedByVsmart", validation_alias="isActivatedByVsmart"
    )


class PolicyDefinitionEditResponse(BaseModel):
    master_templates_affected: List[str] = Field(
        default_factory=list, serialization_alias="masterTemplatesAffected", validation_alias="masterTemplatesAffected"
    )


class PolicyDefinitionPreview(BaseModel):
    preview: str
