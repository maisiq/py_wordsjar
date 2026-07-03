"""create search index

Revision ID: 1876d43d3995
Revises: 506c42677451
Create Date: 2026-07-03 12:39:01.631337

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1876d43d3995'
down_revision: Union[str, Sequence[str], None] = '506c42677451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_index(
        'words_en_text_pattern_ops_idx',
        'words',
        ['en'],
        postgresql_ops={'en': 'text_pattern_ops'}
    )


def downgrade():
    # Удаление индекса
    op.drop_index('words_en_text_pattern_ops_idx', table_name='words')
