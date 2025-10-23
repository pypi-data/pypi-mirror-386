# Copyright 2024 Cisco Systems, Inc. and its affiliates

# mypy: disable-error-code="empty-body"
from uuid import UUID

from catalystwan.endpoints import APIEndpoints, delete, get, post, put, versions
from catalystwan.models.configuration.policy_group import PolicyGroup, PolicyGroupId, PolicyGroupInfo
from catalystwan.typed_list import DataSequence


class PolicyGroupEndpoints(APIEndpoints):
    @post("/v1/policy-group")
    @versions(">=20.12")
    def create_policy_group(self, payload: PolicyGroup) -> PolicyGroupId:
        ...

    @get("/v1/policy-group")
    @versions(">=20.12")
    def get_all(self) -> DataSequence[PolicyGroupInfo]:
        ...

    @put("/v1/policy-group/{group_id}")
    @versions(">=20.12")
    def update(self, group_id: UUID, payload: PolicyGroup) -> None:
        ...

    @delete("/v1/policy-group/{group_id}")
    @versions(">=20.12")
    def delete(self, group_id: UUID) -> None:
        ...
