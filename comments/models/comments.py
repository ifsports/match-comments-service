import uuid

from datetime import datetime, timezone

from sqlalchemy.orm import relationship

from shared.database import Base

from sqlalchemy import Column, UUID, String, DateTime, ForeignKey


class Comment(Base):
    __tablename__ = "comments"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body: str = Column(String(50), nullable=False)
    match_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey("matches.match_id"), nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    match_obj = relationship("Match", back_populates="comments")