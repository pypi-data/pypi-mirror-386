from typing import Callable
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.blood_type import IdentifierType
from ..types.blood_type import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


BLOOD_TYPE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="blood_types", name="Blood Types", slug="blood-types")
    ],
    details=None,
)
