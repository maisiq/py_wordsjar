"""use timestamptz for user_word, cascade on user and word deletion

``last_attempt`` and ``created_at`` were ``timestamp without time zone`` while
the code wrote UTC values into them, so every comparison against a naive
``now()`` (which is local time on the server) was off by the server offset.
They are ``timestamptz`` now, the existing values are interpreted as UTC, and
the frozen ``created_at`` default is replaced by ``now()``.

The foreign keys used to block deleting a user or a word that still had jar
rows; they cascade now.

Revision ID: d3f9a1c72b48
Revises: c8e5d2f41a33
Create Date: 2026-10-31 19:34:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3f9a1c72b48"
down_revision: Union[str, Sequence[str], None] = "c8e5d2f41a33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store the timestamps with a time zone and let jar rows follow their parents."""
    # Values were written as UTC (datetime.now(dt.UTC)), so a naive value is
    # UTC and has to be read as such, not as the server's local time.
    op.execute(
        """
        ALTER TABLE user_word
            ALTER COLUMN last_attempt TYPE timestamptz USING last_attempt AT TIME ZONE 'UTC',
            ALTER COLUMN last_attempt SET DEFAULT now() - interval '1 day',
            ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
            ALTER COLUMN created_at SET DEFAULT now()
        """
    )
    op.execute(
        """
        ALTER TABLE user_word
            DROP CONSTRAINT user_word_user_id_fkey,
            ADD CONSTRAINT user_word_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            DROP CONSTRAINT user_word_word_id_fkey,
            ADD CONSTRAINT user_word_word_id_fkey
                FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
        """
    )
    # The exam query filters by user and orders by rating and the last attempt.
    op.create_index("user_word_exam_idx", "user_word", ["user_id", "rating", "last_attempt"])


def downgrade() -> None:
    """Go back to a naive timestamp, dropping the cascades and the index."""
    op.drop_index("user_word_exam_idx", table_name="user_word")
    op.execute(
        """
        ALTER TABLE user_word
            DROP CONSTRAINT user_word_user_id_fkey,
            ADD CONSTRAINT user_word_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users (id),
            DROP CONSTRAINT user_word_word_id_fkey,
            ADD CONSTRAINT user_word_word_id_fkey
                FOREIGN KEY (word_id) REFERENCES words (id)
        """
    )
    op.execute(
        """
        ALTER TABLE user_word
            ALTER COLUMN last_attempt TYPE timestamp USING last_attempt AT TIME ZONE 'UTC',
            ALTER COLUMN last_attempt SET DEFAULT now() - interval '1 day',
            ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC',
            ALTER COLUMN created_at SET DEFAULT now()
        """
    )