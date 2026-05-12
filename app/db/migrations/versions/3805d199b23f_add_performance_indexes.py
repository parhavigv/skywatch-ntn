"""add performance indexes

Revision ID: 3805d199b23f
Revises: fea294711add
Create Date: 2026-05-11 21:56:08.998371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3805d199b23f'
down_revision: Union[str, Sequence[str], None] = 'fea294711add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
