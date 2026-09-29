\pset null '(null)'
SELECT current_database(), current_user, current_setting('server_version') AS server_version;
SELECT id, login FROM users ORDER BY id;
SELECT id, name, created_by FROM projects ORDER BY id;
SELECT project_id, user_id, role FROM project_members ORDER BY project_id, user_id;
SELECT id, title, description, status, minutes FROM tasks ORDER BY id;
