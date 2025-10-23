# Copyright 2022 Cisco Systems, Inc. and its affiliates

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

from catalystwan.models.policy.policy_list import PolicyListBase, PolicyListId, PolicyListInfo


class ScalableGroupTagListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sgt_name: str = Field(serialization_alias="sgtName", validation_alias="sgtName")
    tag: str = Field(serialization_alias="tag", validation_alias="tag")


class ScalableGroupTagList(PolicyListBase):
    type: Literal["scalablegrouptag", "scalableGroupTag"] = "scalableGroupTag"
    entries: List[ScalableGroupTagListEntry] = Field(default_factory=list)

    def add_entry(self, sgt_name: str, tag: str) -> None:
        self._add_entry(ScalableGroupTagListEntry(sgt_name=sgt_name, tag=tag))


class ScalableGroupTagListEditPayload(ScalableGroupTagList, PolicyListId):
    pass


class ScalableGroupTagListInfo(ScalableGroupTagList, PolicyListInfo):
    pass
