import uuid

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from typing import List

from chats.models.messages import Message

from chats.models.chats import Chat
from chats.schemas.messages import MessageCreateRequest, MessageResponse
from shared.dependencies import get_db
from shared.exceptions import NotFound

router = APIRouter(
    prefix='/api/v1/chat/{chat_id}/messages',
    tags=['Messages']
)


@router.get('/', response_model=List[MessageResponse], status_code=200)
def get_messages(chat_id: uuid.UUID,
                 db: Session = Depends(get_db)):

    chat: Chat = db.query(Chat).filter(Chat.id == chat_id, Chat.finished_at.is_(None)).first() # type: ignore

    if not chat:
        raise NotFound("Chat")

    messages: Message = db.query(Message).filter(Message.chat_id == chat.id)  # type: ignore

    return messages.all()


@router.post('/', response_model=MessageResponse, status_code=201)
def create_message(chat_id: uuid.UUID,
                   message_request: MessageCreateRequest,
                   db: Session = Depends(get_db)):

    message = Message(**message_request.model_dump())
    message.chat_id = chat_id

    chat: Chat = db.query(Chat).filter(Chat.id == chat_id, Chat.finished_at.is_(None)).first() #type: ignore

    if not chat:
        raise NotFound("Chat")

    db.add(message)
    db.commit()
    db.refresh(message)

    return message
