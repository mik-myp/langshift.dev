-- Independent variation: a task has zero or many comments, each by one user.
-- Optional exercise schema, NOT part of the d01-d03-v1 ORM handoff.
CREATE TABLE task_comments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id bigint NOT NULL REFERENCES tasks(id) ON DELETE RESTRICT,
    author_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    body varchar(500) NOT NULL CHECK (length(btrim(body)) > 0)
);
INSERT INTO task_comments (task_id, author_id, body) VALUES (1, 2, 'Reviewed');
SELECT task_id, author_id, body FROM task_comments;
