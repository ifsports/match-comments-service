import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    body: str
    chat_id: uuid.UUID
    user_id: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class MessageCreateRequest(BaseModel):
    body: str
    user_id: str