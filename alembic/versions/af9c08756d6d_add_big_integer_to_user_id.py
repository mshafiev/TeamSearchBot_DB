"""add big integer to user id

Revision ID: af9c08756d6d
Revises: fab10dd7957d
Create Date: 2025-08-11 14:48:10.251829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af9c08756d6d'
down_revision: Union[str, Sequence[str], None] = 'fab10dd7957d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
