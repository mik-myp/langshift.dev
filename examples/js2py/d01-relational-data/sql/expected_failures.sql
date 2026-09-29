-- Deliberate failures: psql continues; each statement is independent (autocommit).
\set ON_ERROR_STOP off
\set VERBOSITY sqlstate
INSERT INTO users (login) VALUES ('alice');
INSERT INTO project_members (project_id, user_id, role) VALUES (1, 9999, 'member');
INSERT INTO tasks (project_id, created_by, title, minutes) VALUES (1, 1, 'Bad', -1);
INSERT INTO tasks (project_id, created_by, title) VALUES (1, 1, NULL);
SELECT count(*) AS tasks_after_failures FROM tasks;
\set ON_ERROR_STOP on
