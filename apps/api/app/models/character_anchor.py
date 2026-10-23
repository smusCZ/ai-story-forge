import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CharacterAnchor(Base):
    __tablename__ = "character_anchors"
    __table_args__ = (
        UniqueConstraint("series_id", "name", name="uq_character_name_per_series"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    appearance_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)
    relationships: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    current_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    consistency_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reference_image_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    series = relationship("Series", back_populates="characters")
