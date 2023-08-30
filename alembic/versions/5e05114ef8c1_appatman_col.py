"""appatman col

Revision ID: 5e05114ef8c1
Revises: 82504e92eb50
Create Date: 2023-08-30 13:18:20.463279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e05114ef8c1'
down_revision: Union[str, None] = '82504e92eb50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('address', sa.Column('appart_num', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('address', 'appart_num')
