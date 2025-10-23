# Copyright 2024 Cisco Systems, Inc. and its affiliates
from typing import List, Literal, Optional

from pydantic import AliasPath, Field

from catalystwan.api.configuration_groups.parcel import Global, _ParcelBase, _ParcelEntry, as_optional_global


class IdentityEntry(_ParcelEntry):
    user: Optional[Global[str]] = Field(default=None)
    user_group: Optional[Global[str]] = Field(
        default=None, validation_alias="userGroup", serialization_alias="userGroup"
    )


class IdentityParcel(_ParcelBase):
    type_: Literal["security-identity"] = Field(default="security-identity", exclude=True)
    entries: List[IdentityEntry] = Field(
        validation_alias=AliasPath("data", "entries"),
        default_factory=list,
        description="Array of Users and User Groups",
    )

    def add_entry(self, user: Optional[str] = None, user_group: Optional[str] = None):
        self.entries.append(
            IdentityEntry(
                user=as_optional_global(user),
                user_group=as_optional_global(user_group),
            )
        )
