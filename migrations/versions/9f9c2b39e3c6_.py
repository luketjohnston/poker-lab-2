"""empty message

Revision ID: 9f9c2b39e3c6
Revises: 758b2acf83f1
Create Date: 2016-10-17 03:34:42.889117

"""

# revision identifiers, used by Alembic.
revision = '9f9c2b39e3c6'
down_revision = '758b2acf83f1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poker_sessions', sa.Column('small_blind', sa.Float(), nullable=True))
    op.drop_column('poker_sessions', 'hand_in_session')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poker_sessions', sa.Column('hand_in_session', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('poker_sessions', 'small_blind')
    ### end Alembic commands ###
