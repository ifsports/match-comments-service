import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import socket_manager
from matches.models.matches import Match
from matches.schemas.matches import MatchRequestUpdateScore, MatchResponse
from messaging.publisher_end_match import publish_match_finished_request
from shared.dependencies import get_db

from shared.exceptions import NotFound

router = APIRouter(
    prefix='/api/v1/matches',
    tags=['Matches']
)

@router.get('/{match_id}', response_model=MatchResponse, status_code=200)
def get_match_details(match_id: uuid.UUID,
                      db: Session = Depends(get_db)):

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

    return match

@router.patch('/{match_id}/start-match', status_code=204)
def start_match(match_id: uuid.UUID,
                db: Session = Depends(get_db)):

    match: Match = db.query(Match).filter(Match.match_id == match_id).first() # type: ignore

    if not match:
        raise NotFound("Partida")

    match.status = "in-progress"

    db.add(match)
    db.commit()
    db.refresh(match)

    return


@router.delete("/{match_id}/end-match", status_code=204)
async def end_match(match_id: uuid.UUID,
                    db: Session = Depends(get_db)):

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

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

@router.patch("/{match_id}/update-score", status_code=204)
async def update_match_score(match_id: uuid.UUID,
                       match_request: MatchRequestUpdateScore,
                       db: Session = Depends(get_db)):

    match: Match = db.query(Match).filter(Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

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