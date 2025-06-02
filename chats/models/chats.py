from datetime import datetime, timezone

from sqlalchemy import Column, UUID, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from chats.models.messages import Message

from shared.database import Base

import uuid

class Chat(Base):
    __tablename__ = "chats"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("matches.match_id"), unique=True, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    finished_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True
    )

    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    match = relationship("Match", back_populates="chat")
