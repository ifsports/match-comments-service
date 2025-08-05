from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import uuid

from typing import List

from auth import get_current_user
from comments.models.comments import Comment
from comments.schemas.comments import CommentResponse, CommentRequest
from app import socket_manager
from shared.auth_utils import has_role
from shared.dependencies import get_db

from shared.exceptions import NotFound
from messaging.audit_publisher import generate_log_payload, run_async_audit

router = APIRouter(
    prefix='/api/v1/matches/{match_id}/comments',
    tags=['Comments']
)


@router.get('/', response_model=List[CommentResponse], status_code=200)
def get_comments(match_id: uuid.UUID,
                 db: Session = Depends(get_db)):
    """
    List Comments by Match

    Lista todos os comentários associados a uma partida específica, identificada pelo `match_id`.

    **Exemplo de Resposta:**

    .. code-block:: json

       [
         {
           "id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
           "match_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
           "body": "Que golaço do time da casa!",
           "created_at": "2025-08-10T14:15:30Z"
         },
         {
           "id": "b2c3d4e5-f6a7-b8c9-d0e1-f2a3b4c5d6e7",
           "match_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
           "body": "Juiz marcou falta, mas não pareceu.",
           "created_at": "2025-08-10T14:18:05Z"
         }
       ]
    """
    comments: Comment = db.query(Comment).filter(
        Comment.match_id == match_id).all()  # type: ignore

    return comments


@router.post('/', response_model=CommentResponse, status_code=201)
async def create_comment(match_id: uuid.UUID,
                         comment_request: CommentRequest,
                         request: Request,
                         db: Session = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    """
    Create a Comment

    Cria um novo comentário para uma partida. A ação é restrita a usuários com o papel 'Organizador'.
    Após a criação, um evento WebSocket (`create_comment`) é emitido para a sala da partida,
    permitindo que clientes atualizem a UI em tempo real. Um log de auditoria também é gerado.

    **Exemplo de Corpo da Requisição (Payload):**

    .. code-block:: json

       {
         "body": "Cartão amarelo para o camisa 5 por reclamação."
       }

    **Exemplo de Resposta:**

    .. code-block:: json

       {
         "id": "d4e5f6a7-b8c9-d0e1-f2a3-b4c5d6e7f8a9",
         "match_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
         "body": "Cartão amarelo para o camisa 5 por reclamação.",
         "created_at": "2025-08-10T14:25:10Z"
       }
    """
    groups = current_user["groups"]

    comment = Comment(**comment_request.model_dump())

    if has_role(groups, "Organizador"):
        comment.match_id = match_id

        db.add(comment)
        db.commit()
        db.refresh(comment)

        comment_data = {
            'match_id': str(comment.match_id),
            'comment_id': str(comment.id),
            'body': comment.body,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
        }

        # Gera o de log de auditoria (comment.created)
        log_payload = generate_log_payload(
            event_type="comment.created",
            service_origin="match_comments_service",
            entity_type="comment",
            entity_id=comment.id,
            operation_type="CREATE",
            campus_code=current_user.get("campus"),
            user_registration=current_user.get("user_matricula"),
            request_object=request,
            new_data=comment_data,
        )

        # Publica o log de auditoria
        run_async_audit(log_payload)

        await socket_manager.emit('create_comment', comment_data, room=str(comment.match_id))

        return comment

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para criar um comentário."
        )


@router.get('/{comment_id}', response_model=CommentResponse, status_code=200)
def comment_details(match_id: uuid.UUID,
                    comment_id: uuid.UUID,
                    db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    """
    Get Comment Details

    Busca os detalhes de um comentário específico pelo seu ID.
    O acesso é restrito a usuários com o papel 'Organizador'.

    **Exemplo de Resposta:**

    .. code-block:: json

       {
         "id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
         "match_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
         "body": "Que golaço do time da casa!",
         "created_at": "2025-08-10T14:15:30Z"
       }
    """
    groups = current_user["groups"]

    comment: Comment = db.query(Comment).filter(
        Comment.match_id == match_id, Comment.id == comment_id).first()  # type: ignore

    if not comment:
        raise NotFound("Comentário")

    if has_role(groups, "Organizador"):
        return comment

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para mostrar os detalhes de um comentário."
        )


@router.put('/{comment_id}', status_code=204)
async def update_comment(match_id: uuid.UUID,
                         comment_id: uuid.UUID,
                         comment_request: CommentRequest,
                         db: Session = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    """
    Update a Comment

    Atualiza o corpo de um comentário existente.
    Após a atualização, um evento WebSocket (`update_comment`) é emitido para a sala da partida.
    Ação restrita a usuários com o papel 'Organizador'. A rota não retorna conteúdo.

    **Exemplo de Corpo da Requisição (Payload):**

    .. code-block:: json

       {
         "body": "Correção: O cartão foi para o camisa 8, não o 5."
       }
    """
    groups = current_user["groups"]

    comment_in = Comment(**comment_request.model_dump())

    comment: Comment = db.query(Comment).filter(
        Comment.match_id == match_id, Comment.id == comment_id).first()  # type: ignore

    if not comment:
        raise NotFound("Comentário")

    if has_role(groups, "Organizador"):
        comment.body = comment_in.body
        db.commit()

        comment_data = {
            'match_id': str(comment.match_id),
            'comment_id': str(comment.id),
            'body': comment.body,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
        }

        await socket_manager.emit('update_comment', comment_data, room=str(comment.match_id))

        return

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para atualizar um comentário."
        )


@router.delete('/{comment_id}', status_code=204)
async def delete_comment(match_id: uuid.UUID,
                         comment_id: uuid.UUID,
                         db: Session = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    """
    Delete a Comment

    Exclui um comentário existente.
    Após a exclusão, um evento WebSocket (`delete_comment`) é emitido para a sala da partida.
    Ação restrita a usuários com o papel 'Organizador'. A rota não retorna conteúdo.
    """
    groups = current_user["groups"]

    comment: Comment = db.query(Comment).filter(
        Comment.match_id == match_id, Comment.id == comment_id).first()  # type: ignore

    if not comment:
        raise NotFound("Comentário")

    if has_role(groups, "Organizador"):
        db.delete(comment)
        db.commit()

        comment_data = {
            'match_id': str(comment.match_id),
            'comment_id': str(comment.id),
            'body': comment.body,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
        }

        await socket_manager.emit('delete_comment', comment_data, room=str(comment.match_id))

        return

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para excluir um comentário."
        )
