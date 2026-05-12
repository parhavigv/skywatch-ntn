"""add performance indexes

Revision ID: e2955b09a532
Revises: 3805d199b23f
Create Date: 2026-05-11 21:57:15.397973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2955b09a532'
down_revision: Union[str, Sequence[str], None] = '3805d199b23f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
