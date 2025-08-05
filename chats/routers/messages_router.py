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
    """
    List Messages in a Chat

    Lista todas as mensagens de uma sala de chat específica.

    **Exemplo de Resposta:**

    .. code-block:: json

       [
         {
           "id": "f1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6",
           "chat_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
           "user_id": "20231012030011",
           "body": "Bom dia! Alguém sabe que horas começa o jogo?",
           "created_at": "2025-08-10T09:30:00Z"
         },
         {
           "id": "e1f2a3b4-c5d6-e7f8-a9b0-c1d2e3f4a5b6",
           "chat_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
           "user_id": "20221012030005",
           "body": "Acho que é às 14h.",
           "created_at": "2025-08-10T09:32:15Z"
         }
       ]
    """
    chat: Chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.finished_at.is_(None)).first()  # type: ignore

    if not chat:
        raise NotFound("Chat")

    messages = db.query(Message).filter(
        Message.chat_id == chat.id)  # type: ignore

    return messages.all()


@router.post('/', response_model=MessageResponse, status_code=201)
async def create_message(chat_id: uuid.UUID,
                         message_request: MessageCreateRequest,
                         db: Session = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    """
    Create a Message

    Envia uma nova mensagem para uma sala de chat.
    - A ação é restrita a usuários com o papel 'Organizador' ou 'Jogador'.
    - Após o envio, um evento WebSocket (`new_message`) é emitido para a sala da partida
      associada ao chat, permitindo a atualização em tempo real para os clientes.

    **Exemplo de Corpo da Requisição (Payload):**

    .. code-block:: json

       {
         "body": "O jogo foi confirmado para as 14h. Não se atrasem!"
       }

    **Exemplo de Resposta:**

    .. code-block:: json

       {
         "id": "d4e5f6a7-b8c9-d0e1-f2a3-b4c5d6e7f8a9",
         "chat_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
         "user_id": "20211012030001",
         "body": "O jogo foi confirmado para as 14h. Não se atrasem!",
         "created_at": "2025-08-10T10:05:00Z"
       }
    """
    groups = current_user["groups"]
    user_id = current_user["user_matricula"]

    message = Message(**message_request.model_dump())

    if has_role(groups, "Organizador", "Jogador"):
        message.chat_id = chat_id
        message.user_id = user_id

        chat: Chat = db.query(Chat).filter(
            Chat.id == chat_id, Chat.finished_at.is_(None)).first()  # type: ignore

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
