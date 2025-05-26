import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatResponse(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
