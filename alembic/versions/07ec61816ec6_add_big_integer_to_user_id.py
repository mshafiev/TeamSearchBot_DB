"""add big integer to user id

Revision ID: 07ec61816ec6
Revises: af9c08756d6d
Create Date: 2025-08-11 14:52:32.846619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07ec61816ec6'
down_revision: Union[str, Sequence[str], None] = 'af9c08756d6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
