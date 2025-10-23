from datetime import datetime, UTC
from sqlalchemy import DateTime, String, Uuid, Computed, event, text
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from bluecore_models.models.base import Base


class ResourceBase(Base):
    __tablename__ = "resource_base"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[bytes] = mapped_column(JSONB, nullable=False)
    uuid: Mapped[Uuid] = mapped_column(Uuid, nullable=True, unique=True, index=True)
    uri: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    data_vector: Mapped[bytes] = mapped_column(
        TSVECTOR, Computed(text("to_tsvector('english', data)"))
    )

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "resource_base",
    }


# ==============================================================================
# Ensure created_at and updated_at are exactly the same when inserting.
# (if created_at time not present)
# ------------------------------------------------------------------------------
@event.listens_for(ResourceBase, "before_insert", propagate=True)
def set_created_and_updated(mapper, connection, target):
    now = datetime.now(UTC)
    if not target.created_at:
        target.created_at = now
    if not target.updated_at:
        target.updated_at = now
