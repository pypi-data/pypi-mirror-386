from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import ipaddress

    from .context import RequestContext
    from .schema import MainSchemaTypes


@runtime_checkable
class RelatedNodeBase(Protocol):
    @property
    def id(self) -> str | None: ...

    @property
    def hfid(self) -> list[Any] | None: ...

    @property
    def hfid_str(self) -> str | None: ...

    @property
    def is_resource_pool(self) -> bool: ...

    @property
    def initialized(self) -> bool: ...

    @property
    def display_label(self) -> str | None: ...

    @property
    def typename(self) -> str | None: ...

    def _generate_input_data(self, allocate_from_pool: bool = False) -> dict[str, Any]: ...

    def _generate_mutation_query(self) -> dict[str, Any]: ...

    @classmethod
    def _generate_query_data(cls, peer_data: dict[str, Any] | None = None, property: bool = False) -> dict: ...


@runtime_checkable
class RelatedNode(RelatedNodeBase, Protocol): ...


@runtime_checkable
class RelatedNodeSync(RelatedNodeBase, Protocol): ...


@runtime_checkable
class Attribute(Protocol):
    name: str
    id: str | None
    is_default: bool | None
    is_from_profile: bool | None
    is_inherited: bool | None
    updated_at: str | None
    is_visible: bool | None
    is_protected: bool | None


class String(Attribute):
    value: str


class StringOptional(Attribute):
    value: str | None


class DateTime(Attribute):
    value: str


class DateTimeOptional(Attribute):
    value: str | None


class HashedPassword(Attribute):
    value: str


class HashedPasswordOptional(Attribute):
    value: Any


class URL(Attribute):
    value: str


class URLOptional(Attribute):
    value: str | None


class MacAddress(Attribute):
    value: str


class MacAddressOptional(Attribute):
    value: str | None


class Dropdown(Attribute):
    value: str


class DropdownOptional(Attribute):
    value: str | None


class Enum(Attribute):
    value: str


class EnumOptional(Attribute):
    value: str | None


class Integer(Attribute):
    value: int


class IntegerOptional(Attribute):
    value: int | None


class IPHost(Attribute):
    value: ipaddress.IPv4Address | ipaddress.IPv6Address


class IPHostOptional(Attribute):
    value: ipaddress.IPv4Address | ipaddress.IPv6Address | None


class IPNetwork(Attribute):
    value: ipaddress.IPv4Network | ipaddress.IPv6Network


class IPNetworkOptional(Attribute):
    value: ipaddress.IPv4Network | ipaddress.IPv6Network | None


class Boolean(Attribute):
    value: bool


class BooleanOptional(Attribute):
    value: bool | None


class ListAttribute(Attribute):
    value: list[Any]


class ListAttributeOptional(Attribute):
    value: list[Any] | None


class JSONAttribute(Attribute):
    value: Any


class JSONAttributeOptional(Attribute):
    value: Any | None


class AnyAttribute(Attribute):
    value: float


class AnyAttributeOptional(Attribute):
    value: float | None


@runtime_checkable
class CoreNodeBase(Protocol):
    _schema: MainSchemaTypes
    _internal_id: str
    id: str  # NOTE this is incorrect, should be str | None
    display_label: str | None
    typename: str | None

    @property
    def hfid(self) -> list[str] | None: ...

    @property
    def hfid_str(self) -> str | None: ...

    def get_human_friendly_id(self) -> list[str] | None: ...

    def get_human_friendly_id_as_string(self, include_kind: bool = False) -> str | None: ...

    def get_kind(self) -> str: ...

    def get_all_kinds(self) -> list[str]: ...

    def get_branch(self) -> str: ...

    def is_ip_prefix(self) -> bool: ...

    def is_ip_address(self) -> bool: ...

    def is_resource_pool(self) -> bool: ...

    def get_raw_graphql_data(self) -> dict | None: ...


@runtime_checkable
class CoreNode(CoreNodeBase, Protocol):
    async def save(
        self,
        allow_upsert: bool = False,
        update_group_context: bool | None = None,
        timeout: int | None = None,
        request_context: RequestContext | None = None,
    ) -> None: ...

    async def delete(self, timeout: int | None = None, request_context: RequestContext | None = None) -> None: ...

    async def update(
        self, do_full_update: bool, timeout: int | None = None, request_context: RequestContext | None = None
    ) -> None: ...

    async def create(
        self, allow_upsert: bool = False, timeout: int | None = None, request_context: RequestContext | None = None
    ) -> None: ...

    async def add_relationships(self, relation_to_update: str, related_nodes: list[str]) -> None: ...

    async def remove_relationships(self, relation_to_update: str, related_nodes: list[str]) -> None: ...


@runtime_checkable
class CoreNodeSync(CoreNodeBase, Protocol):
    def save(
        self,
        allow_upsert: bool = False,
        update_group_context: bool | None = None,
        timeout: int | None = None,
        request_context: RequestContext | None = None,
    ) -> None: ...

    def delete(self, timeout: int | None = None, request_context: RequestContext | None = None) -> None: ...

    def update(
        self, do_full_update: bool, timeout: int | None = None, request_context: RequestContext | None = None
    ) -> None: ...

    def create(
        self, allow_upsert: bool = False, timeout: int | None = None, request_context: RequestContext | None = None
    ) -> None: ...

    def add_relationships(self, relation_to_update: str, related_nodes: list[str]) -> None: ...

    def remove_relationships(self, relation_to_update: str, related_nodes: list[str]) -> None: ...
