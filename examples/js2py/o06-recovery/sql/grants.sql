-- Runtime identity for this read/create-project operational slice, NOT a superuser.
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO lab_app;
GRANT SELECT ON users, auth_sessions TO lab_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON projects, project_members, tasks TO lab_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lab_app;
GRANT SELECT ON alembic_version TO lab_app;
