-- Add day_residue column to dreams.dreams
-- Stores the previous day's waking-life context that may have seeded the dream.
-- Optional field — null if not provided by the user.

ALTER TABLE dreams.dreams
    ADD COLUMN IF NOT EXISTS day_residue text;
