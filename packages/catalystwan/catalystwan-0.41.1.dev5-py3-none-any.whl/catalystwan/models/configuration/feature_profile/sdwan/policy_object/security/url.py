# Copyright 2024 Cisco Systems, Inc. and its affiliates

from typing import List, Literal

from pydantic import AliasPath, ConfigDict, Field

from catalystwan.api.configuration_groups.parcel import Global, _ParcelBase, _ParcelEntry, as_global


class BaseURLListEntry(_ParcelEntry):
    model_config = ConfigDict(populate_by_name=True)
    pattern: Global[str]


class URLParcel(_ParcelBase):
    model_config = ConfigDict(populate_by_name=True)
    type_: Literal["security-urllist"] = Field(default="security-urllist", exclude=True)
    type: Literal["urlallowed", "urlblocked"]
    entries: List[BaseURLListEntry] = Field(default_factory=list, validation_alias=AliasPath("data", "entries"))

    def add_url(self, pattern: str):
        self.entries.append(BaseURLListEntry(pattern=as_global(pattern)))


class URLAllowParcel(URLParcel):
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["urlallowed"] = "urlallowed"


class URLBlockParcel(URLParcel):
    model_config = ConfigDict(populate_by_name=True)
    type: Literal["urlblocked"] = "urlblocked"
