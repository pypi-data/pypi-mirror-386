"""Database abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Type, TypeVar

import fastapi
import pydantic
from bson.objectid import ObjectId
from pydantic_core import core_schema

T = TypeVar("T", bound="DatabaseItem")


class ForeignKey(Generic[T]):
    """A reference to another DatabaseItem."""

    def __init__(self, target_type: type[T], identifier: str):
        self.target_type = target_type
        self.identifier = identifier

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ForeignKey)
            and self.target_type == other.target_type
            and self.identifier == other.identifier
        )

    def __hash__(self) -> int:
        return hash((self.target_type, self.identifier))

    def __repr__(self) -> str:
        return f"ForeignKey({self.target_type.__name__}:{self.identifier})"

    @classmethod
    def __class_getitem__(cls, item: type[T]):
        target_type = item

        class _ForeignKey(cls):  # type: ignore
            __origin__ = cls
            __args__ = (item,)

            @classmethod
            def __get_pydantic_core_schema__(cls, source_type, handler: pydantic.GetCoreSchemaHandler):
                def validator(v):
                    if isinstance(v, ForeignKey):
                        return v
                    if isinstance(v, target_type):
                        return ForeignKey(target_type, v.identifier)
                    if isinstance(v, str):
                        return ForeignKey(target_type, v)
                    raise TypeError(f"Cannot convert {v!r} to ForeignKey[{target_type.__name__}]")

                return core_schema.no_info_after_validator_function(
                    validator,
                    core_schema.union_schema(
                        [
                            core_schema.is_instance_schema(target_type),
                            core_schema.str_schema(),
                            core_schema.is_instance_schema(ForeignKey),
                        ]
                    ),
                )

            @classmethod
            def __get_pydantic_json_schema__(cls, _core_schema, handler):
                return handler(core_schema.str_schema())

        return _ForeignKey


class PydanticObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic v2 compatibility.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: pydantic.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate, core_schema.any_schema(), serialization=core_schema.plain_serializer_function_ser_schema(str)
        )

    @classmethod
    def validate(cls, value: Any) -> PydanticObjectId:
        """Validate PydanticObjectId, accepting strings and ObjectIds."""
        if isinstance(value, ObjectId):
            return cls(value)
        if isinstance(value, str) and ObjectId.is_valid(value):
            return cls(value)
        raise ValueError(f"Invalid ObjectId: {value}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __repr__(self) -> str:
        return "Pydantic" + super().__repr__()


class DatabaseItem(ABC, pydantic.BaseModel):
    """Base class for database items."""

    model_config = pydantic.ConfigDict(revalidate_instances="always", populate_by_name=True, from_attributes=True)

    identifier: PydanticObjectId = pydantic.Field(alias="_id", default_factory=PydanticObjectId)

    # @pydantic.field_serializer("identifier")
    # def serialize_identifier(self, identifier: PydanticObjectId, _info):
    #     return str(identifier)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DatabaseItem):
            return NotImplemented
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)


class Database(ABC):
    """Database abstraction."""

    @abstractmethod
    async def upsert(self, item: DatabaseItem) -> None:
        """Update entity or create if it does not exist."""

    @abstractmethod
    async def get(self, class_type: Type[T], identifier: PydanticObjectId) -> T:
        """Return entity, raise UnknownEntityError if entity does not exist."""

    @abstractmethod
    async def get_all(self, class_type: Type[T]) -> List[T]:
        """Return all entities of collection, raise UnknownEntityError if no entities found."""

    @abstractmethod
    async def delete(self, class_type: Type[T], identifier: PydanticObjectId, cascade: bool = False) -> None:
        """Delete entity, raise UnknownEntityError if entity does not exist."""

    @abstractmethod
    async def find(self, class_type: Type[T], **kwargs: str) -> List[T]:
        """Return all entities of collection matching the filter criteria,
        raise UnknownEntityError if entity does not exist."""

    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""

    @abstractmethod
    async def purge(self) -> None:
        """Purge all collections in the database."""


def create_api_router(db: Database, class_types: List[Type[DatabaseItem]]) -> fastapi.APIRouter:
    """Create a FastAPI router for the database."""
    router = fastapi.APIRouter()

    for class_type in class_types:
        class_name = class_type.__name__.lower()

        def create_get_item(cls_name: str, cls_type: Type[DatabaseItem]):
            @router.get(f"/{cls_name}/{{identifier}}", response_model=cls_type)
            async def get_item(identifier: PydanticObjectId) -> cls_type:  # type: ignore
                """Get a single item by ID."""
                try:
                    return (await db.get(cls_type, identifier)).model_dump()
                except UnknownEntityError as exc:
                    raise fastapi.HTTPException(status_code=404, detail="Item not found") from exc

            return get_item  # type: ignore

        def create_upsert_item(cls_name: str, cls_type: Type[DatabaseItem]):
            @router.post(f"/{cls_name}")
            async def upsert_item(request: fastapi.Request) -> None:
                data = await request.json()
                await db.upsert(cls_type.model_validate(data))

            return upsert_item

        def create_delete_item(cls_name: str, cls_type: Type[DatabaseItem]):
            @router.delete(f"/{cls_name}/{{identifier}}")
            async def delete_item(identifier: str) -> None:
                """Delete an item by ID."""
                try:
                    await db.delete(cls_type, PydanticObjectId(identifier))
                except UnknownEntityError as exc:
                    raise fastapi.HTTPException(status_code=404, detail="Item not found") from exc

            return delete_item

        def create_get_all(cls_name: str, cls_type: Type[DatabaseItem]):
            @router.get(f"/{cls_name}/", response_model=List[cls_type])
            async def get_all() -> List[cls_type]:  # type: ignore
                """Get all items."""
                try:
                    return await db.get_all(cls_type)
                except UnknownEntityError as exc:
                    raise fastapi.HTTPException(404) from exc

            return get_all  # type: ignore

        def create_find(cls_name: str, cls_type: Type[DatabaseItem]):
            @router.get(f"/{cls_name}", response_model=List[cls_type])
            async def find(request: fastapi.Request) -> List[DatabaseItem]:
                """Find items by criteria."""
                try:
                    return await db.find(cls_type, **request.query_params)
                except UnknownEntityError as exc:
                    raise fastapi.HTTPException(404, detail=f"{cls_name} not found for specified arguments") from exc

            return find

        create_get_item(class_name, class_type)
        create_upsert_item(class_name, class_type)
        create_delete_item(class_name, class_type)
        create_get_all(class_name, class_type)
        create_find(class_name, class_type)

    return router


class DatabaseError(Exception):
    """Errors related to database operations."""


class UnknownEntityError(DatabaseError):
    """Requested entity does not exist."""
