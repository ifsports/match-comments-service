import uuid

from chats.models.chats import Chat
from matches.models.matches import Match
from shared.dependencies import get_db


def create_match_comments_in_db(message_data: dict) -> dict:
    """
    Função síncrona para criar Match_Comments no banco de dados.
    """
    db_gen = get_db()
    db = next(db_gen)

    try:
        match_id_str = message_data.get("match_id")
        team_home_id_str = message_data.get("team_home_id")
        team_away_id_str = message_data.get("team_away_id")
        status_str = message_data.get("status")

        if not match_id_str:
            raise ValueError("'match_id' é obrigatório na mensagem")
        if not team_home_id_str:
            raise ValueError("'team_home_id' é obrigatório na mensagem")
        if not team_away_id_str:
            raise ValueError("'team_away_id' é obrigatório na mensagem")

        try:
            match_id_for_db = uuid.UUID(match_id_str)
        except ValueError:
            raise ValueError(f"match_id'{match_id_str}' não é um UUID válido")

        try:
            team_home_id_for_db = uuid.UUID(team_home_id_str)
        except ValueError:
            raise ValueError(f"team_home_id '{team_home_id_str}' não é um UUID válido")

        try:
            team_away_id_for_db = uuid.UUID(team_away_id_str)
        except ValueError:
            raise ValueError(f"team_away_id '{team_away_id_str}' não é um UUID válido")

        print(
            f"DB_SYNC: Processando match para match_id: {match_id_for_db}, team_home_id: {team_home_id_for_db}, team_away_id: {team_away_id_for_db}, status: {status_str}")


        filters = [
            Match.match_id == match_id_for_db,
            Match.team_home_id == team_home_id_for_db,
            Match.team_away_id == team_away_id_for_db,
        ]

        existing_match: Match = db.query(Match).filter(*filters).first()

        if existing_match:
            print(
                f"DB_SYNC: Partida já existe (ID: {existing_match.match_id}). Nenhuma nova partida será criada.")
            return {
                "message": "Partida já existente processada como duplicada.",
                "request_id": existing_match.match_id
            }

        print(f"DB_SYNC: Criando nova partida...")

        match_creation_data = {
            "match_id": match_id_for_db,
            "team_home_id": team_home_id_for_db,
            "team_away_id": team_away_id_for_db,
            "score_home": 0,
            "score_away": 0,
            "status": status_str,
        }

        new_match = Match(**match_creation_data)

        db.add(new_match)
        db.commit()
        db.refresh(new_match)

        chat = Chat(match_id=new_match.match_id)

        db.add(chat)
        db.commit()
        db.refresh(chat)

        print(f"DB_SYNC: Match ID {new_match.match_id}")

        return {
            "match_id": new_match.match_id,
            "team_home_id": new_match.team_home_id,
            "team_away_id": new_match.team_away_id,
            "status": status_str,
        }
    except Exception as e:
        db.rollback()
        print(f"DB_SYNC: Erro ao criar request no banco: {e}")
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass