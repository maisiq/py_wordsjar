"""normalise words and make them unique per lowercase form

Words are looked up by exact match, so "Apple" and "apple" used to be two
different words: the dictionary contained both. This migration merges such
pairs (keeping the lowest id, merging the ratings of the user rows) and then
makes the situation impossible with a unique index on ``lower(btrim(en))``.

Revision ID: c8e5d2f41a33
Revises: b4a7c1e5d920
Create Date: 2026-10-31 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e5d2f41a33"
down_revision: Union[str, Sequence[str], None] = "b4a7c1e5d920"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_merge_duplicates = """
CREATE TEMP TABLE _word_duplicate ON COMMIT DROP AS
SELECT w.id AS dup_id, d.keep_id
FROM words w
JOIN (
    SELECT lower(btrim(en)) AS key, min(id) AS keep_id
    FROM words
    GROUP BY 1
    HAVING count(*) > 1
) d ON lower(btrim(w.en)) = d.key
WHERE w.id <> d.keep_id;

-- Keep the best of both rows when a user has both versions in the jar.
UPDATE user_word uw
SET rating = greatest(uw.rating, src.rating),
    attempts = greatest(uw.attempts, src.attempts),
    last_attempt = least(uw.last_attempt, src.last_attempt)
FROM user_word src
JOIN _word_duplicate d ON d.dup_id = src.word_id
WHERE uw.user_id = src.user_id AND uw.word_id = d.keep_id;

-- Re-point the rows that do not collide with an existing one.
UPDATE user_word uw
SET word_id = d.keep_id
FROM _word_duplicate d
WHERE uw.word_id = d.dup_id
  AND NOT EXISTS (
      SELECT 1 FROM user_word x
      WHERE x.user_id = uw.user_id AND x.word_id = d.keep_id
  );

DELETE FROM user_word uw USING _word_duplicate d WHERE uw.word_id = d.dup_id;
DELETE FROM words w USING _word_duplicate d WHERE w.id = d.dup_id;
"""


def upgrade() -> None:
    """Merge case-insensitive duplicates and enforce one spelling per word."""
    op.execute(_merge_duplicates)
    op.execute("UPDATE words SET en = lower(btrim(en)) WHERE en <> lower(btrim(en))")
    op.execute("CREATE UNIQUE INDEX words_en_lower_key ON words (lower(btrim(en)))")


def downgrade() -> None:
    """Drop the guard index.

    The merged duplicates are not restored: they were the same word.
    """
    op.execute("DROP INDEX words_en_lower_key")