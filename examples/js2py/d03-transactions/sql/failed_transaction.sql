-- Deliberate failure. This whole file must run on ONE connection.
\set ON_ERROR_STOP off
\set VERBOSITY sqlstate
BEGIN;
INSERT INTO projects(name, created_by) VALUES ('Broken SQL', 1);
INSERT INTO project_members(project_id, user_id, role)
SELECT id, 9999, 'owner' FROM projects WHERE name='Broken SQL';
SELECT count(*) FROM projects;
ROLLBACK;
SELECT count(*) AS broken_remaining FROM projects WHERE name='Broken SQL';
SELECT 1 AS connection_recovered;
\set ON_ERROR_STOP on
