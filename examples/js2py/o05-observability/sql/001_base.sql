-- Teaching contract d01-d03-v1 (2026-09-28). Apply only to the owned lab database.
CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login varchar(80) NOT NULL UNIQUE,
    CONSTRAINT users_login_nonblank CHECK (length(btrim(login)) > 0)
);

CREATE TABLE projects (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(120) NOT NULL,
    created_by bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT projects_name_nonblank CHECK (length(btrim(name)) > 0)
);

CREATE TABLE project_members (
    project_id bigint NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    role varchar(8) NOT NULL,
    PRIMARY KEY (project_id, user_id),
    CONSTRAINT project_members_role_valid CHECK (role IN ('owner', 'member'))
);

CREATE TABLE tasks (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    created_by bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title varchar(120) NOT NULL,
    description varchar(2000),
    status varchar(8) NOT NULL DEFAULT 'todo',
    minutes integer NOT NULL DEFAULT 0,
    due_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tasks_title_nonblank CHECK (length(btrim(title)) > 0),
    CONSTRAINT tasks_status_valid CHECK (status IN ('todo', 'doing', 'done')),
    CONSTRAINT tasks_minutes_nonnegative CHECK (minutes >= 0)
);

