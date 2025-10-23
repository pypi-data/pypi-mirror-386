# Copyright 2023 Cisco Systems, Inc. and its affiliates

from typing import Any, List, Literal, Optional, Union, overload
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Annotated

from catalystwan.models.policy.policy import (
    AssemblyItemBase,
    PolicyCreationPayload,
    PolicyDefinition,
    PolicyEditPayload,
    PolicyInfo,
)

TrafficDataDirection = Literal[
    "service",
    "tunnel",
    "all",
    "from-service",
    "from-tunnel",
]

ControlDirection = Literal[
    "in",
    "out",
]

AppRouteItemType = Literal["approute", "appRoute"]


def assert_feature_defintion(definition: Any) -> "CentralizedPolicyDefinition":
    assert isinstance(definition, CentralizedPolicyDefinition)
    return definition


class DataApplicationEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    direction: TrafficDataDirection = "service"
    site_lists: Optional[List[UUID]] = Field(
        default=None, serialization_alias="siteLists", validation_alias="siteLists"
    )
    vpn_lists: List[UUID] = Field(default_factory=list, serialization_alias="vpnLists", validation_alias="vpnLists")
    region_ids: Optional[List[str]] = Field(default=None, serialization_alias="regionIds", validation_alias="regionIds")
    region_lists: Optional[List[UUID]] = Field(
        default=None, serialization_alias="regionLists", validation_alias="regionLists"
    )

    # def apply_site_list(self, site_list_id: UUID):
    #     self.site_lists.append(site_list_id)

    # def apply_vpn_list(self, vpn_list_id: UUID):
    #     self.vpn_lists.append(vpn_list_id)


class ControlApplicationEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    direction: ControlDirection
    site_lists: Optional[List[UUID]] = Field(
        default=None, serialization_alias="siteLists", validation_alias="siteLists"
    )
    region_lists: Optional[List[UUID]] = Field(
        default=None, serialization_alias="regionLists", validation_alias="regionLists"
    )
    region_ids: Optional[List[str]] = Field(default=None, serialization_alias="regionIds", validation_alias="regionIds")


class ControlPolicyItem(AssemblyItemBase):
    type: Literal["control"] = "control"
    entries: List[ControlApplicationEntry] = []

    def assign_to_inbound_sites(self, site_lists: List[UUID]) -> None:
        entry = ControlApplicationEntry(direction="in", site_lists=site_lists)
        self.entries.append(entry)

    def assign_to_outbound_sites(self, site_lists: List[UUID]) -> None:
        entry = ControlApplicationEntry(direction="out", site_lists=site_lists)
        self.entries.append(entry)

    @overload
    def assign_to_inbound_regions(self, *, region_ids: List[int]) -> None:
        ...

    @overload
    def assign_to_inbound_regions(self, *, region_lists: List[UUID]) -> None:
        ...

    def assign_to_inbound_regions(
        self, *, region_ids: Optional[List[int]] = None, region_lists: Optional[List[UUID]] = None
    ) -> None:
        _region_ids = [str(rid) for rid in region_ids] if region_ids else None
        entry = entry = ControlApplicationEntry(direction="in", region_ids=_region_ids, region_lists=region_lists)
        self.entries.append(entry)

    @overload
    def assign_to_outbound_regions(self, *, region_ids: List[int]) -> None:
        ...

    @overload
    def assign_to_outbound_regions(self, *, region_lists: List[UUID]) -> None:
        ...

    def assign_to_outbound_regions(
        self, *, region_ids: Optional[List[int]] = None, region_lists: Optional[List[UUID]] = None
    ) -> None:
        _region_ids = [str(rid) for rid in region_ids] if region_ids else None
        entry = entry = ControlApplicationEntry(direction="out", region_ids=_region_ids, region_lists=region_lists)
        self.entries.append(entry)


class TrafficDataPolicyItem(AssemblyItemBase):
    type: Literal["data"] = "data"
    entries: List[DataApplicationEntry] = []

    @overload
    def assign_to(
        self,
        vpn_lists: List[UUID],
        direction: TrafficDataDirection = "service",
        *,
        site_lists: List[UUID],
    ) -> None:
        ...

    @overload
    def assign_to(
        self,
        vpn_lists: List[UUID],
        direction: TrafficDataDirection = "service",
        *,
        region_lists: List[UUID],
    ) -> None:
        ...

    @overload
    def assign_to(
        self,
        vpn_lists: List[UUID],
        direction: TrafficDataDirection = "service",
        *,
        region_ids: List[int],
    ) -> None:
        ...

    def assign_to(
        self,
        vpn_lists: List[UUID],
        direction: TrafficDataDirection = "service",
        *,
        site_lists: Optional[List[UUID]] = None,
        region_lists: Optional[List[UUID]] = None,
        region_ids: Optional[List[int]] = None,
    ) -> None:
        entry = DataApplicationEntry(
            direction=direction,
            site_lists=site_lists,
            vpn_lists=vpn_lists,
            region_lists=region_lists,
            region_ids=[str(rid) for rid in region_ids] if region_ids else None,
        )
        self.entries.append(entry)


class HubAndSpokePolicyItem(AssemblyItemBase):
    type: Literal["hubAndSpoke"] = "hubAndSpoke"


class MeshPolicyItem(AssemblyItemBase):
    type: Literal["mesh"] = "mesh"


class AppRoutePolicyItem(AssemblyItemBase):
    type: AppRouteItemType = "appRoute"
    entries: List[DataApplicationEntry] = []


class CFlowDPolicyItem(AssemblyItemBase):
    type: Literal["cflowd"] = "cflowd"


class VpnMembershipGroupPolicyItem(AssemblyItemBase):
    type: Literal["vpnMembershipGroup"] = "vpnMembershipGroup"


AnyAssemblyItem = Annotated[
    Union[
        TrafficDataPolicyItem,
        ControlPolicyItem,
        MeshPolicyItem,
        HubAndSpokePolicyItem,
        AppRoutePolicyItem,
        CFlowDPolicyItem,
        VpnMembershipGroupPolicyItem,
    ],
    Field(discriminator="type"),
]


class CentralizedPolicyDefinition(PolicyDefinition):
    model_config = ConfigDict(populate_by_name=True)
    region_role_assembly: List = Field(
        default_factory=list, serialization_alias="regionRoleAssembly", validation_alias="regionRoleAssembly"
    )
    assembly: List[AnyAssemblyItem] = []
    model_config = ConfigDict(populate_by_name=True)

    def find_assembly_item_by_definition_id(self, definition_id: UUID) -> Optional[AnyAssemblyItem]:
        for item in self.assembly:
            if item.definition_id == definition_id:
                return item
        return None


class CentralizedPolicy(PolicyCreationPayload):
    model_config = ConfigDict(populate_by_name=True)
    policy_type: Literal["feature", "cli"] = Field(
        default="feature", serialization_alias="policyType", validation_alias="policyType"
    )
    policy_definition: Union[str, CentralizedPolicyDefinition] = Field(
        serialization_alias="policyDefinition",
        validation_alias="policyDefinition",
    )

    def add_traffic_data_policy(self, traffic_data_policy_id: UUID) -> TrafficDataPolicyItem:
        policy_definition = assert_feature_defintion(self.policy_definition)
        item = TrafficDataPolicyItem(definition_id=traffic_data_policy_id)
        policy_definition.assembly.append(item)
        return item

    def add_control_policy(self, control_policy_id: UUID) -> ControlPolicyItem:
        policy_definition = assert_feature_defintion(self.policy_definition)
        item = ControlPolicyItem(definition_id=control_policy_id)
        policy_definition.assembly.append(item)
        return item

    def add_mesh_policy(self, mesh_policy_id: UUID) -> None:
        policy_definition = assert_feature_defintion(self.policy_definition)
        policy_definition.assembly.append(MeshPolicyItem(definition_id=mesh_policy_id))

    def add_hub_and_spoke_policy(self, hub_and_spoke_policy_id: UUID) -> None:
        policy_definition = assert_feature_defintion(self.policy_definition)
        policy_definition.assembly.append(HubAndSpokePolicyItem(definition_id=hub_and_spoke_policy_id))

    @model_validator(mode="before")
    @classmethod
    def try_parse_policy_definition_string(cls, values):
        # this is needed because GET /template/policy/vsmart contains string in policyDefinition field
        # while POST /template/policy/vsmart requires a regular object
        # it makes sense to reuse that model for both requests and present parsed data to the user
        if not isinstance(values, dict):
            return values
        json_policy_type = values.get("policyType")
        json_policy_definition = values.get("policyDefinition")
        if json_policy_type == "feature" and isinstance(json_policy_definition, str):
            values["policyDefinition"] = CentralizedPolicyDefinition.model_validate_json(json_policy_definition)
        return values


class CentralizedPolicyEditPayload(PolicyEditPayload, CentralizedPolicy):
    rid: Optional[int] = Field(default=None, serialization_alias="@rid", validation_alias="@rid")


class CentralizedPolicyInfo(PolicyInfo, CentralizedPolicyEditPayload):
    pass
