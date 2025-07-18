from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(
    prefix='/api/v1/matches/{match_id}/comments',
    tags=['Comments']
)


@router.get('/', response_model=List[CommentResponse], status_code=200)
def get_comments(match_id: uuid.UUID,
                 db: Session = Depends(get_db)):

    comments: Comment = db.query(Comment).filter(Comment.match_id == match_id).all() # type: ignore

    return comments

@router.post('/', response_model=CommentResponse, status_code=201)
async def create_comment(match_id: uuid.UUID,
                   comment_request: CommentRequest,
                   db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):

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

    groups = current_user["groups"]

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

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

    groups = current_user["groups"]

    comment_in = Comment(**comment_request.model_dump())

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

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

    groups = current_user["groups"]

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

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