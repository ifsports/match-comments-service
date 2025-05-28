from pydantic import BaseModel

import uuid

from datetime import datetime


class CommentResponse(BaseModel):
    id: uuid.UUID
    body: str
    match_id: uuid.UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class CommentRequest(BaseModel):
    body: str