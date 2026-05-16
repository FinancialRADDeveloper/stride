-- Add optional assignee field to tasks.
-- SQLite allows ADD COLUMN for nullable columns without rebuilding the table.
ALTER TABLE tasks ADD COLUMN assignee TEXT;
