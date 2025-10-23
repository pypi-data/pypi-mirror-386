# Copyright 2024 Cisco Systems, Inc. and its affiliates
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from catalystwan.models.common import check_fields_exclusive
from catalystwan.models.policy.policy_list import PolicyListBase, PolicyListId, PolicyListInfo


class AppListEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_family: Optional[str] = Field(default=None, serialization_alias="appFamily", validation_alias="appFamily")
    app: Optional[str] = None

    @model_validator(mode="after")
    def check_app_xor_appfamily(self):
        check_fields_exclusive(self.__dict__, {"app", "app_family"}, True)
        return self


class AppList(PolicyListBase):
    type: Literal["app"] = "app"
    entries: List[AppListEntry] = []

    def add_app(self, app: str) -> None:
        self._add_entry(AppListEntry(app=app))

    def add_app_family(self, app_family: str) -> None:
        self._add_entry(AppListEntry(app_family=app_family))

    def list_all_app(self) -> List[str]:
        return [e.app for e in self.entries if e.app is not None]

    def list_all_app_family(self) -> List[str]:
        return [e.app_family for e in self.entries if e.app_family is not None]


class AppListEditPayload(AppList, PolicyListId):
    pass


class AppListInfo(AppList, PolicyListInfo):
    pass
