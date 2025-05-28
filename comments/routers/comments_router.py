from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import uuid

from typing import List

from comments.models.comments import Comment
from comments.schemas.comments import CommentResponse, CommentRequest
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
def create_comment(match_id: uuid.UUID,
                   comment_request: CommentRequest,
                   db: Session = Depends(get_db)):

    comment = Comment(**comment_request.model_dump())
    comment.match_id = match_id

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


@router.get('/{comment_id}', response_model=CommentResponse, status_code=200)
def comment_details(match_id: uuid.UUID,
                    comment_id: uuid.UUID,
                    db: Session = Depends(get_db)):

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

    if not comment:
        raise NotFound("Comentário")

    return comment


@router.put('/{comment_id}', status_code=204)
def update_comment(match_id: uuid.UUID,
                   comment_id: uuid.UUID,
                   comment_request: CommentRequest,
                   db: Session = Depends(get_db)):

    comment_in = Comment(**comment_request.model_dump())

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

    if not comment:
        raise NotFound("Comentário")

    comment.body = comment_in.body
    db.commit()

    return


@router.delete('/{comment_id}', status_code=204)
def delete_comment(match_id: uuid.UUID,
                   comment_id: uuid.UUID,
                   db: Session = Depends(get_db)):

    comment: Comment = db.query(Comment).filter(Comment.match_id == match_id, Comment.id == comment_id).first() # type: ignore

    if not comment:
        raise NotFound("Comentário")

    db.delete(comment)
    db.commit()

    return