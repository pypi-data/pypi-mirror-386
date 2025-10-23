# Copyright 2024 Cisco Systems, Inc. and its affiliates

from typing import List, Literal

from pydantic import AliasPath, ConfigDict, Field

from catalystwan.api.configuration_groups.parcel import Global, _ParcelBase, _ParcelEntry, as_global


class ProtocolListEntry(_ParcelEntry):
    model_config = ConfigDict(populate_by_name=True)
    protocol: Global[str] = Field(serialization_alias="protocolName", validation_alias="protocolName")


class ProtocolListParcel(_ParcelBase):
    model_config = ConfigDict(populate_by_name=True)
    type_: Literal["security-protocolname"] = Field(default="security-protocolname", exclude=True)
    entries: List[ProtocolListEntry] = Field(default_factory=list, validation_alias=AliasPath("data", "entries"))

    def add_protocol(self, protocol: str):
        self.entries.append(ProtocolListEntry(protocol=as_global(protocol)))
