"""make category description nullable

Revision ID: 8be903f282d1
Revises: 709d2d94ac8c
Create Date: 2026-10-12 00:20:28.439696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8be903f282d1'
down_revision: Union[str, Sequence[str], None] = '709d2d94ac8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'categories', 
        'description', 
        existing_type=sa.Text(), 
        nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'categories', 
        'description', 
        existing_type=sa.Text(), 
        nullable=False
    )
