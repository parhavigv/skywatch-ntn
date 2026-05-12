"""add performance indexes

Revision ID: 4b8da756befd
Revises: e2955b09a532
Create Date: 2026-05-11 21:58:30.109593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b8da756befd'
down_revision: Union[str, Sequence[str], None] = 'e2955b09a532'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
