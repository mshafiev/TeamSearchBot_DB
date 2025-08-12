"""update int to str in tg_d

Revision ID: 6c0212b76b70
Revises: 07ec61816ec6
Create Date: 2025-08-11 15:02:25.072417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c0212b76b70'
down_revision: Union[str, Sequence[str], None] = '07ec61816ec6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
