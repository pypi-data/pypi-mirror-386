# Copyright 2024 Cisco Systems, Inc. and its affiliates

from typing import List, Literal

from pydantic import AliasPath, ConfigDict, Field

from catalystwan.api.configuration_groups.parcel import Global, _ParcelBase, _ParcelEntry, as_global


class FQDNListEntry(_ParcelEntry):
    model_config = ConfigDict(populate_by_name=True)
    pattern: Global[str] = Field(
        description="Ex: cisco.com, .*cisco.com, .*.cisco.com. Should not start with '*' or '+'"
    )


class FQDNDomainParcel(_ParcelBase):
    model_config = ConfigDict(populate_by_name=True)
    type_: Literal["security-fqdn"] = Field(default="security-fqdn", exclude=True)
    entries: List[FQDNListEntry] = Field(default_factory=list, validation_alias=AliasPath("data", "entries"))

    def from_fqdns(self, fqdns: List[str]):
        for fqdn in fqdns:
            self.entries.append(FQDNListEntry(pattern=as_global(fqdn)))
