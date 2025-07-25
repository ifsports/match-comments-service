import uuid

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session

from typing import List

from auth import get_current_user
from chats.models.messages import Message

from chats.models.chats import Chat
from chats.schemas.messages import MessageCreateRequest, MessageResponse
from app import socket_manager
from shared.auth_utils import has_role
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

    messages = db.query(Message).filter(Message.chat_id == chat.id)  # type: ignore

    return messages.all()


@router.post('/', response_model=MessageResponse, status_code=201)
async def create_message(chat_id: uuid.UUID,
                   message_request: MessageCreateRequest,
                   db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):

    groups = current_user["groups"]
    user_id = current_user["user_matricula"]

    message = Message(**message_request.model_dump())

    if has_role(groups, "Organizador", "Jogador"):
        message.chat_id = chat_id
        message.user_id = user_id

        chat: Chat = db.query(Chat).filter(Chat.id == chat_id, Chat.finished_at.is_(None)).first() #type: ignore

        if not chat:
            raise NotFound("Chat")

        db.add(message)
        db.commit()
        db.refresh(message)

        message_data = {
            'chat_id': str(message.chat_id),
            'message_id': str(message.id),
            'body': message.body,
            'user_id': message.user_id,
            'created_at': message.created_at.isoformat() if message.created_at else None,
        }

        await socket_manager.emit('new_message', message_data, room=str(chat.match_id))

        return message

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para criar uma mensagem."
        )