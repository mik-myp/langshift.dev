INSERT INTO users (login) VALUES ('alice'), ('bob');
INSERT INTO projects (name, created_by) VALUES
    ('Launch', 1), ('Docs', 2), ('Empty', 1);
INSERT INTO project_members (project_id, user_id, role) VALUES
    (1, 1, 'owner'), (1, 2, 'member'), (2, 2, 'owner'), (3, 1, 'owner');
INSERT INTO tasks
    (project_id, created_by, title, description, status, minutes,
     created_at, updated_at)
VALUES
    (1, 1, 'Design API', NULL, 'todo', 30,
     '2026-09-28 09:00:00+00', '2026-09-28 09:00:00+00'),
    (1, 2, 'Add tests', '', 'doing', 45,
     '2026-09-28 09:00:00+00', '2026-09-28 09:00:00+00'),
    (1, 1, 'Ship demo', 'reviewed', 'done', 15,
     '2026-09-28 09:00:00+00', '2026-09-28 09:00:00+00'),
    (2, 2, 'Read SQL', NULL, 'todo', 20,
     '2026-09-28 09:00:00+00', '2026-09-28 09:00:00+00'),
    (2, 2, 'Write guide', 'draft', 'done', 40,
     '2026-09-28 09:00:00+00', '2026-09-28 09:00:00+00');
