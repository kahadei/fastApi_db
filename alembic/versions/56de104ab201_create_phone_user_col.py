"""create phone user col

Revision ID: 56de104ab201
Revises: 
Create Date: 2023-08-30 11:15:42.326881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56de104ab201'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_num', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone_num')
