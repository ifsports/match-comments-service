import uuid

from datetime import datetime, timezone

from shared.database import Base

from sqlalchemy import Column, UUID, String, DateTime

class Comment(Base):
    __tablename__ = "comments"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body: str = Column(String(50), nullable=False)
    match_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )