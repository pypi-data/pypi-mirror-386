# Copyright 2024 Cisco Systems, Inc. and its affiliates

from typing import Any, Dict, Generic, List, Literal, Optional, Sequence, Tuple, TypeVar

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from pydantic.alias_generators import to_camel
from typing_extensions import get_origin

from catalystwan.exceptions import CatalystwanException
from catalystwan.models.common import VersionedField

T = TypeVar("T")


class _ParcelEntry(BaseModel):
    def __hash__(self) -> int:
        return hash(self.model_dump_json())


class _ParcelBase(BaseModel):
    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, populate_by_name=True, json_schema_mode_override="validation"
    )
    parcel_name: str = Field(
        min_length=1,
        max_length=128,
        pattern=r'^[^&<>! "]+$',
        serialization_alias="name",
        validation_alias="name",
    )
    parcel_description: Optional[str] = Field(
        default=None,
        serialization_alias="description",
        validation_alias="description",
        description="Set the parcel description",
    )
    data: Optional[Any] = None
    entries: Optional[Sequence[_ParcelEntry]] = Field(default=None, validation_alias=AliasPath("data", "entries"))
    _parcel_data_key: str = PrivateAttr(default="data")

    @model_serializer(mode="wrap")
    def envelope_parcel_data(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Dict[str, Any]:
        """
        serializes model fields with respect to field validation_alias,
        sub-classing parcel fields can be defined like following:
        >>> entries: List[SecurityZoneListEntry] = Field(default=[], validation_alias=AliasPath("data", "entries"))

        "data" is default _parcel_data_key which must match validation_alias prefix,
        this attribute can be overriden in sub-class when needed
        """
        model_dict = handler(self)
        model_dict[self._parcel_data_key] = {}
        remove_keys = []
        replaced_keys: Dict[str, Tuple[str, str]] = {}

        # enveloping
        for key in model_dict.keys():
            field_info = self.model_fields.get(key)
            if field_info and isinstance(field_info.validation_alias, AliasPath):
                aliases = field_info.validation_alias.convert_to_aliases()
                if aliases and aliases[0] == self._parcel_data_key and len(aliases) == 2:
                    model_dict[self._parcel_data_key][aliases[1]] = model_dict[key]
                    replaced_keys[key] = (self._parcel_data_key, str(aliases[1]))
                    remove_keys.append(key)
        for key in remove_keys:
            del model_dict[key]

        # versioned field update
        model_dict = VersionedField.dump(self.model_fields, model_dict, info, replaced_keys)

        return model_dict

    @classmethod
    def _get_parcel_type(cls) -> str:
        field_info = cls.model_fields.get("type_")
        if field_info is not None:
            return str(field_info.default)
        raise CatalystwanException(f"{cls.__name__} field parcel type is not set.")

    def remove_duplicated_entries(self) -> None:
        if self.entries:
            self.entries = list(set(self.entries))


# https://github.com/pydantic/pydantic/discussions/6090
# Usage: Global[str](value="test")
class Global(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    option_type: Literal["global"] = "global"
    value: T

    def __bool__(self) -> bool:
        # if statements use __len__ when __bool__ is not defined
        return True

    def __len__(self) -> int:
        if isinstance(self.value, (str, list)):
            return len(self.value)
        return -1

    def __ge__(self, other: Any) -> bool:
        if isinstance(self.value, int):
            return self.value >= other
        return False

    def __le__(self, other: Any) -> bool:
        if isinstance(self.value, int):
            return self.value <= other
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class Variable(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    option_type: Literal["variable"] = "variable"
    value: str = Field(pattern=r"^\{\{[.\/\[\]a-zA-Z0-9_-]+\}\}$", min_length=1, max_length=64)


class Default(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    option_type: Literal["default"] = "default"
    value: Optional[T] = None


def as_optional_global(value: Any, generic_alias: Any = None):
    if value is None:
        return None

    return as_global(value, generic_alias)


def as_global(value: Any, generic_alias: Any = None):
    """Produces Global object given only value (type is induced from value)

    Args:
        value (Any): value of Global object to be produced
        generic_alias (Any, optional): specify alias type like Literal. Defaults to None.

    Returns:
        Global[Any]: global option type object
    """
    if generic_alias is None:
        if isinstance(value, list):
            if len(value) == 0:
                return Global[List](value=list())  # type: ignore
            return Global[List[type(value[0])]](value=value)  # type: ignore
        return Global[type(value)](value=value)  # type: ignore
    elif get_origin(generic_alias) is Literal:
        return Global[generic_alias](value=value)  # type: ignore
    raise TypeError(
        f"Inappropriate type origin: {generic_alias} {get_origin(generic_alias)} for argument generic_alias"
    )


def as_variable(value: str):
    """Produces Variable object from variable name string

    Args:
        value (str): value of Variable object to be produced

    Returns:
        Variable: variable option type object
    """
    if not value.startswith("{{") and not value.endswith("}}"):
        value = "{{" + value + "}}"
    return Variable(value=value)


def as_default(value: Any, generic_alias: Any = None):
    """Produces Default object given only value (type is induced from value)

    Args:
        value (Any): value of Default object to be produced
        generic_alias (Any, optional): specify alias type like Literal. Defaults to None.

    Returns:
        Default[Any]: default option type object
    """
    if value is None:
        return Default[None](value=None)
    if generic_alias is None:
        if isinstance(value, list):
            if len(value) == 0:
                return Default[List](value=list())  # type: ignore
            return Default[List[type(value[0])]](value=value)  # type: ignore
        return Default[type(value)](value=value)  # type: ignore
    elif get_origin(generic_alias) is Literal:
        return Default[generic_alias](value=value)  # type: ignore
    raise TypeError(
        f"Inappropriate type origin: {generic_alias} {get_origin(generic_alias)} for argument generic_alias"
    )


def as_optional_global_or_variable(value: Any, generic_alias: Any = None):
    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        return as_variable(value)
    else:
        return as_optional_global(value, generic_alias)
