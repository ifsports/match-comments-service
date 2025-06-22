"""Make start_time nullable in matches

Revision ID: c5d07e5767ff
Revises: 1bbd7f1315d1
Create Date: 2025-06-22 00:36:13.252521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d07e5767ff'
down_revision: Union[str, None] = '1bbd7f1315d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'matches',
        'start_time',
        existing_type=sa.TIMESTAMP(timezone=True),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'matches',
        'start_time',
        existing_type=sa.TIMESTAMP(timezone=True),
        nullable=False
    )
