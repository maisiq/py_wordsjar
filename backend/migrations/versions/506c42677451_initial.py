"""initial

Revision ID: 506c42677451
Revises: 
Create Date: 2026-06-10 12:28:24.133544

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '506c42677451'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table('users',
    sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.Text(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('words',
    sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('en', sa.String(), nullable=False),
    sa.Column('ru', sa.ARRAY(sa.String()), nullable=False),
    sa.Column('transcription', sa.String(), nullable=False),
    sa.Column('examples', sa.ARRAY(sa.String()), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('en')
    )
    op.create_table('user_word',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('word_id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Float(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('last_attempt', sa.DateTime(), server_default=sa.text("NOW() - INTERVAL '1 day'"), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default='NOW()', nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'word_id')
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('user_word')
    op.drop_table('words')
    op.drop_table('users')
