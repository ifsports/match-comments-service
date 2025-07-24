import uuid

from pydantic import BaseModel


class MatchRequestUpdateScore(BaseModel):
    score_home: int
    score_away: int

class MatchResponse(BaseModel):
    match_id: uuid.UUID
    competition_id: uuid.UUID
    team_home_id: uuid.UUID
    team_away_id: uuid.UUID
    score_home: int
    score_away: int
    status: str