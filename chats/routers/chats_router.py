from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from chats.models.chats import Chat
from chats.schemas.chats import ChatResponse

from shared.exceptions import NotFound, Conflict
from shared.dependencies import get_db

router = APIRouter(
    prefix='/api/v1/matches/{match_id}/chat',
    tags=['Chats']
)


@router.get('/', response_model=ChatResponse, status_code=200)
def chat_details(match_id: str,
                 db: Session = Depends(get_db)):
    """
    Get Chat Details by Match

    Retorna os detalhes da sala de chat associada a uma partida específica.
    Cada partida possui uma única sala de chat.

    **Exemplo de Resposta:**

    .. code-block:: json

       {
         "id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
         "match_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
         "created_at": "2025-08-10T13:59:00Z",
         "finished_at": null
       }
    """
    chat: Chat = db.query(Chat).filter(
        Chat.match_id == match_id).first()  # type: ignore

    if not chat:
        raise NotFound("Chat")

    return chat
