import uuid
from datetime import datetime

from sqlalchemy import Column, UUID, DateTime, String, Integer
from sqlalchemy.orm import relationship

from comments.models.comments import Comment

from shared.database import Base

class Match(Base):
    __tablename__ = "matches"

    match_id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    team_home_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    team_away_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    score_home: int = Column(Integer, nullable=False)
    score_away: int = Column(Integer, nullable=False)
    start_time: datetime = Column(
        DateTime(timezone=True),
        nullable=True
    )
    status: str = Column(String(50), nullable=False)

    comments = relationship("Comment", back_populates="match_obj")
    chat = relationship("Chat", back_populates="match")