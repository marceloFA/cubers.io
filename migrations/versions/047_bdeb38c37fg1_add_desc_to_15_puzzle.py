"""Add description for 15 puzzle

Revision ID: bdeb38c37fg1
Revises: 05923bad79cf
Create Date: 2020-10-23 14:23:00.123969

"""
from sqlalchemy.sql import table, column
from sqlalchemy import String
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bdeb38c37fg1'
down_revision = '05923bad79cf'
branch_labels = None
depends_on = None

def upgrade():
    events = table('events', column('name', String), column('description', String))
    op.execute(events.update().where(events.c.name == op.inline_literal('15 Puzzle')).values({'description': op.inline_literal('<p>U = Up</p><p>D = Down</p><p>R = Right</p><p>L = Left</p><p>Scramble by moving the piece U/D/L/R relative to the empty space, into the empty space.</p><p>Moves like R3 indicate to perform an R move 3 times.</p>')}))

def downgrade():
    events = table('events', column('name', String), column('description', String))
    op.execute(events.update().where(events.c.name == op.inline_literal('15 Puzzle')).values({'description': op.inline_literal('')}))
