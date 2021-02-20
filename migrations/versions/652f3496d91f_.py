"""empty message

Revision ID: 652f3496d91f
Revises: cd621b59fb97
Create Date: 2021-02-19 18:43:30.399971

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '652f3496d91f'
down_revision = 'cd621b59fb97'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'date',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=50),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'date',
               existing_type=sa.String(length=50),
               type_=sa.INTEGER(),
               existing_nullable=False)
    # ### end Alembic commands ###
