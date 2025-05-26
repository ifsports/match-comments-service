from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from chats.models.chats import Chat
from chats.schemas.chats import ChatResponse
from chats.shared.dependencies import get_db
from chats.shared.exceptions import NotFound, Conflict

router = APIRouter(
    prefix='/api/v1/matches/{match_id}/chat',
    tags=['Chats']
)


@router.get('/', response_model=ChatResponse, status_code=200)
def chat_details(match_id: str,
                 db: Session = Depends(get_db)):

    chat: Chat = db.query(Chat).filter(Chat.match_id == match_id).first() # type: ignore

    if not chat:
        raise NotFound("Chat")

    return chat


@router.post('/', response_model=ChatResponse,status_code=201)
def create_chat(match_id: str,
                db: Session = Depends(get_db)):

    chat_exists: Chat = db.query(Chat).filter(Chat.match_id == match_id).first() # type: ignore

    if chat_exists:
        raise Conflict("Conflito")

    chat: Chat = Chat(match_id=match_id)

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


