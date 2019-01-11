"""remove blacklist table and add blacklist flag to userEventResults

Revision ID: 3371f5156029
Revises: dd535b1f37a1
Create Date: 2019-01-06 19:19:53.234270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3371f5156029'
down_revision = 'dd535b1f37a1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blacklist', schema=None) as batch_op:
        batch_op.drop_index('ix_blacklist_comp_id')

    op.drop_table('blacklist')
    with op.batch_alter_table('user_event_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('blacklist_note', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('is_blacklisted', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_event_results', schema=None) as batch_op:
        batch_op.drop_column('is_blacklisted')
        batch_op.drop_column('blacklist_note')

    op.create_table('blacklist',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('comp_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['comp_id'], ['competitions.id'], name='blacklist_comp_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='blacklist_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='blacklist_pkey')
    )
    with op.batch_alter_table('blacklist', schema=None) as batch_op:
        batch_op.create_index('ix_blacklist_comp_id', ['comp_id'], unique=False)

    # ### end Alembic commands ###