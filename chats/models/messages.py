from datetime import datetime, timezone

from sqlalchemy import Column, UUID, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from shared.database import Base

import uuid


class Message(Base):
    __tablename__ = "messages"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body: str = Column(String, nullable=False)
    chat_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("chats.id"),
        nullable=False
    )
    user_id: str = Column(String, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    chat = relationship("Chat", back_populates="messages")