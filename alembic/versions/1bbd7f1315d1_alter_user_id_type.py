"""alter user_id type

Revision ID: 1bbd7f1315d1
Revises: 0db50924a7fd
Create Date: 2025-06-03 10:37:39.969308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1bbd7f1315d1'
down_revision: Union[str, None] = '0db50924a7fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter user_id column from UUID to String
    op.alter_column('messages', 'user_id',
                    existing_type=postgresql.UUID(),
                    type_=sa.String(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert user_id column from String back to UUID
    op.alter_column('messages', 'user_id',
                    existing_type=sa.String(),
                    type_=postgresql.UUID(),
                    existing_nullable=False)