"""adds cascade removal in models

Revision ID: fe24c5010053
Revises: c5d07e5767ff
Create Date: 2025-06-27 14:08:53.807403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe24c5010053'
down_revision: Union[str, None] = 'c5d07e5767ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Atualizar constraint de chats.match_id para CASCADE
    op.drop_constraint('chats_match_id_fkey', 'chats', type_='foreignkey')
    op.create_foreign_key(
        'chats_match_id_fkey',
        'chats', 'matches',
        ['match_id'], ['match_id'],
        ondelete='CASCADE'
    )

    # Atualizar constraint de messages.chat_id para CASCADE
    op.drop_constraint('messages_chat_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_chat_id_fkey',
        'messages', 'chats',
        ['chat_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Reverter constraint de chats.match_id (remover CASCADE)
    op.drop_constraint('chats_match_id_fkey', 'chats', type_='foreignkey')
    op.create_foreign_key(
        'chats_match_id_fkey',
        'chats', 'matches',
        ['match_id'], ['match_id']
    )

    # Reverter constraint de messages.chat_id (remover CASCADE)
    op.drop_constraint('messages_chat_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_chat_id_fkey',
        'messages', 'chats',
        ['chat_id'], ['id']
    )
