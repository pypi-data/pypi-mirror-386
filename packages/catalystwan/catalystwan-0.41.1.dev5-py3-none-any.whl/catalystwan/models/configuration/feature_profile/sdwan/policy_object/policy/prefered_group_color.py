# Copyright 2024 Cisco Systems, Inc. and its affiliates

from typing import List, Literal, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator, model_validator

from catalystwan.api.configuration_groups.parcel import Global, _ParcelBase, _ParcelEntry, as_global
from catalystwan.models.common import TLOCColor

PathPreference = Literal[
    "direct-path",
    "multi-hop-path",
    "all-paths",
]


class Preference(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    color_preference: Global[List[TLOCColor]] = Field(
        serialization_alias="colorPreference", validation_alias="colorPreference"
    )
    path_preference: Global[PathPreference] = Field(
        serialization_alias="pathPreference", validation_alias="pathPreference"
    )


class PreferredColorGroupEntry(_ParcelEntry):
    model_config = ConfigDict(populate_by_name=True)
    primary_preference: Preference = Field(
        serialization_alias="primaryPreference", validation_alias="primaryPreference"
    )
    secondary_preference: Optional[Preference] = Field(
        None, serialization_alias="secondaryPreference", validation_alias="secondaryPreference"
    )
    tertiary_preference: Optional[Preference] = Field(
        None, serialization_alias="tertiaryPreference", validation_alias="tertiaryPreference"
    )

    @model_validator(mode="after")
    def check_passwords_match(self) -> "PreferredColorGroupEntry":
        if not self.secondary_preference and self.tertiary_preference:
            raise ValueError("Preference Entry has to have a secondary prefrence when assigning tertiary preference.")
        return self

    @field_validator("secondary_preference", "tertiary_preference", mode="before")
    @classmethod
    def remove_empty_preferences(cls, value):
        """handle a situation when server returns empty json object: '{}'"""
        if not value:
            return None
        return value


class PreferredColorGroupParcel(_ParcelBase):
    model_config = ConfigDict(populate_by_name=True)
    type_: Literal["preferred-color-group"] = Field(default="preferred-color-group", exclude=True)
    entries: List[PreferredColorGroupEntry] = Field(default_factory=list, validation_alias=AliasPath("data", "entries"))

    def add_primary(self, color_preference: List[TLOCColor], path_preference: PathPreference):
        self.entries.append(
            PreferredColorGroupEntry(
                primary_preference=Preference(
                    color_preference=Global[List[TLOCColor]](value=color_preference),
                    path_preference=as_global(path_preference, PathPreference),
                ),
                secondary_preference=None,
                tertiary_preference=None,
            )
        )

    def add_secondary(self, color_preference: List[TLOCColor], path_preference: PathPreference):
        preferred_color = self.entries[0]
        preferred_color.secondary_preference = Preference(
            color_preference=Global[List[TLOCColor]](value=color_preference),
            path_preference=as_global(path_preference, PathPreference),
        )

    def add_tertiary(self, color_preference: List[TLOCColor], path_preference: PathPreference):
        preferred_color = self.entries[0]
        preferred_color.tertiary_preference = Preference(
            color_preference=Global[List[TLOCColor]](value=color_preference),
            path_preference=as_global(path_preference, PathPreference),
        )
