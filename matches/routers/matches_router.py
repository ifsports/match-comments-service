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


@router.get("/", response_model=List[MatchResponse])
def get_matches(competition_id: str = Query(..., description="Filtrar partidas por competição"),
                limit: int = Query(
                    6, ge=1, le=100, description="Número máximo de partidas por página"),
                offset: int = Query(
                    0, ge=0, description="Número de partidas a pular"),
                db: Session = Depends(get_db)):
    """
    List Matches by Competition

    Lista as partidas de uma competição específica. O parâmetro `competition_id` é obrigatório.
    A lista é ordenada para mostrar primeiro as partidas "em progresso" e depois por data de início.
    A rota suporta paginação através dos parâmetros `limit` e `offset`.

    **Exemplo de Resposta:**

    .. code-block:: json

       [
         {
           "match_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
           "competition_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
           "team_home_id": "d1e2f3a4-b5c6-d7e8-f9a0-b1c2d3e4f5a6",
           "team_away_id": "e1f2a3b4-c5d6-e7f8-a9b0-c1d2e3f4a5b6",
           "score_home": 1,
           "score_away": 0,
           "status": "in-progress",
           "start_time": "2025-08-10T14:00:00Z",
           "round": 1
         },
         {
           "match_id": "b2c3d4e5-f6a7-b8c9-d0e1-f2a3b4c5d6e7",
           "competition_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
           "team_home_id": "f1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6",
           "team_away_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
           "score_home": 0,
           "score_away": 0,
           "status": "not-started",
           "start_time": "2025-08-10T16:00:00Z",
           "round": 1
         }
       ]
    """
    if not competition_id:
        raise HTTPException(
            status_code=400,
            detail="O ID da competição deve ser informado!"
        )

    query = db.query(Match).filter(Match.competition_id == competition_id)
    query = query.order_by(
        (Match.status == "in-progress").desc(),
        Match.start_time.asc()
    )

    matches = query.offset(offset).limit(limit).all()

    return matches


@router.get('/{match_id}', response_model=MatchResponse, status_code=200)
def get_match_details(match_id: uuid.UUID,
                      db: Session = Depends(get_db)):
    """
    Get Match Details

    Busca os detalhes de uma partida específica pelo seu ID.

    **Exemplo de Resposta:**

    .. code-block:: json

       {
         "match_id": "a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6",
         "competition_id": "c1d2e3f4-a5b6-7890-1234-567890abcdef",
         "team_home_id": "d1e2f3a4-b5c6-d7e8-f9a0-b1c2d3e4f5a6",
         "team_away_id": "e1f2a3b4-c5d6-e7f8-a9b0-c1d2e3f4a5b6",
         "score_home": 1,
         "score_away": 0,
         "status": "in-progress",
         "start_time": "2025-08-10T14:00:00Z",
         "round": 1
       }
    """
    match: Match = db.query(Match).filter(
        Match.match_id == match_id).first()  # type: ignore

    if not match:
        raise NotFound("Partida")

    return match


@router.patch('/{match_id}/start-match', status_code=204)
def start_match(match_id: uuid.UUID,
                db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    """
    Start a Match

    Inicia uma partida, alterando seu status para 'in-progress'.
    Esta é uma ação restrita a usuários com o papel 'Organizador'.
    A rota não retorna conteúdo no corpo da resposta.
    """
    groups = current_user["groups"]

    match: Match = db.query(Match).filter(
        Match.match_id == match_id).first()  # type: ignore

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
    """
    End a Match

    Finaliza uma partida. Esta ação:
    1. Altera o status da partida para 'finished'.
    2. Publica uma mensagem para notificar outros serviços sobre o resultado.
    3. Remove o registro da partida da tabela de partidas ativas.

    Esta é uma ação restrita a usuários com o papel 'Organizador'.
    A rota não retorna conteúdo no corpo da resposta.
    """
    groups = current_user["groups"]

    match: Match = db.query(Match).filter(
        Match.match_id == match_id).first()  # type: ignore

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
    """
    Update Match Score

    Atualiza o placar de uma partida em andamento.
    Após a atualização, um evento WebSocket (`score_updated`) é emitido para a sala
    correspondente ao `match_id`, permitindo que clientes atualizem a UI em tempo real.
    Esta é uma ação restrita a usuários com o papel 'Organizador'.

    **Exemplo de Corpo da Requisição (Payload):**

    .. code-block:: json

       {
         "score_home": 2,
         "score_away": 1
       }
    """
    groups = current_user["groups"]

    match: Match = db.query(Match).filter(
        Match.match_id == match_id).first()  # type: ignore

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
