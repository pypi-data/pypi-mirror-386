from typing import Callable
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.organization_role import IdentifierType
from ..types.organization_role import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


ORGANIZATION_ROLE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="organization_roles",
            name="Organization Roles",
            slug="organization-roles",
        )
    ],
    details=None,
)
