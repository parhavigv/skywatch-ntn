"""add performance indexes

Revision ID: 718ada1a10ef
Revises: 4b8da756befd
Create Date: 2026-05-12 15:16:01.656309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '718ada1a10ef'
down_revision: Union[str, Sequence[str], None] = '4b8da756befd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
