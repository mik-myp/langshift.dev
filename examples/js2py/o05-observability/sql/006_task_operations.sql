CREATE TABLE task_operations(
    actor_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    project_id bigint NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    operation varchar(32) NOT NULL,
    key uuid NOT NULL,
    request_digest varchar(64) NOT NULL,
    response_body jsonb NOT NULL,
    response_status smallint NOT NULL,
    created_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    PRIMARY KEY(actor_id,project_id,operation,key),
    CONSTRAINT task_operations_expiry_order CHECK(expires_at > created_at),
    CONSTRAINT task_operations_status CHECK(response_status = 201),
    CONSTRAINT task_operations_digest_format CHECK(request_digest ~ '^[0-9a-f]{64}$')
);
CREATE INDEX task_operations_expires_at_idx ON task_operations(expires_at);
