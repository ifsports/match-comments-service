import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import socket_manager
from auth import get_current_user
from matches.models.matches import Match
from matches.schemas.matches import MatchRequestUpdateScore, MatchResponse
from messaging.publisher_end_match import publish_match_finished_request
from shared.auth_utils import has_role
from shared.dependencies import get_db

from shared.exceptions import NotFound

router = APIRouter(
    prefix='/api/v1/matches',
    tags=['Matches']
)

@router.get('/', response_model=List[MatchResponse], status_code=200)
def get_matches(competition_id: Optional[str] = Query(None, description="Filtrar partidas por competição"),
                db: Session = Depends(get_db)):


    if not competition_id:
        raise HTTPException(
            status_code=400,
            detail="O ID da competição deve ser informado!"
        )

    matches = db.query(Match).filter(Match.competition_id == competition_id).all()

    return matches

@router.get('/{match_id}', response_model=MatchResponse, status_code=200)
def get_match_details(match_id: uuid.UUID,
                      db: Session = Depends(get_db)):

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

    return match

@router.patch('/{match_id}/start-match', status_code=204)
def start_match(match_id: uuid.UUID,
                db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):

    groups = current_user["groups"]

    match: Match = db.query(Match).filter(Match.match_id == match_id).first() # type: ignore

    if not match:
        raise NotFound("Partida")

    if has_role(groups, "Organizador"):
        match.status = "in-progress"

        db.add(match)
        db.commit()
        db.refresh(match)

        return

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para iniciar uma partida."
        )


@router.delete("/{match_id}/end-match", status_code=204)
async def end_match(match_id: uuid.UUID,
                    db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):

    groups = current_user["groups"]

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

    if has_role(groups, "Organizador"):
        match.status = "finished"

        match_message_data = {
            "match_id": str(match.match_id),
            "team_home_id": str(match.team_home_id),
            "team_away_id": str(match.team_away_id),
            "score_home": match.score_home,
            "score_away": match.score_away,
            "status": match.status
        }

        await publish_match_finished_request(match_message_data)

        db.delete(match)
        db.commit()

        return

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para finalizar uma partida."
        )

@router.patch("/{match_id}/update-score", status_code=204)
async def update_match_score(match_id: uuid.UUID,
                       match_request: MatchRequestUpdateScore,
                       db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):

    groups = current_user["groups"]

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

    if has_role(groups, "Organizador"):
        match.score_home = match_request.score_home
        match.score_away = match_request.score_away

        db.add(match)
        db.commit()
        db.refresh(match)

        match_data = {
            "match_id": str(match.match_id),
            "team_home_id": str(match.team_home_id),
            "team_away_id": str(match.team_away_id),
            "score_home": match.score_home,
            "score_away": match.score_away,
            "status": match.status
        }

        await socket_manager.emit('score_updated', match_data, room=str(match.match_id))

        return

    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para atualizar o placar de uma partida."
        )