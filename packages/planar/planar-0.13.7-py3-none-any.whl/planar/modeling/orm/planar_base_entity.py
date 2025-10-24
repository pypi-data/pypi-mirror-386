from pydantic import ConfigDict
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper

from planar.logging import get_logger
from planar.modeling.mixins.auditable import AuditableMixin
from planar.modeling.mixins.uuid_primary_key import UUIDPrimaryKeyMixin

from .reexports import SQLModel

logger = get_logger("orm.PlanarBaseEntity")


# Default schema for all entity / user tables, but can be overridden by the user
# in planar configuration, which db.py uses.
PLANAR_ENTITY_SCHEMA = "planar_entity"
PLANAR_APPLICATION_METADATA = MetaData(schema=PLANAR_ENTITY_SCHEMA)


class PlanarBaseEntity(UUIDPrimaryKeyMixin, AuditableMixin, SQLModel, table=False):
    __abstract__ = True
    model_config = ConfigDict(validate_assignment=True)  # type: ignore
    metadata = PLANAR_APPLICATION_METADATA


@event.listens_for(PlanarBaseEntity, "before_delete", propagate=True)
def log_deletion(
    mapper: Mapper, connection: Connection, target: PlanarBaseEntity
) -> None:
    """Logs the deletion of the entity."""
    logger.info("deleting entity", table_name=target.__tablename__, key=target.id)
