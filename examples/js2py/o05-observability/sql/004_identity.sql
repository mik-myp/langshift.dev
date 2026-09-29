ALTER TABLE users ADD COLUMN password_hash text,
    ADD COLUMN is_active boolean NOT NULL DEFAULT false,
    ADD COLUMN auth_version bigint NOT NULL DEFAULT 1,
    ADD COLUMN created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN password_changed_at timestamptz,
    ADD CONSTRAINT users_auth_version_positive CHECK(auth_version >= 1),
    ADD CONSTRAINT users_active_password CHECK(NOT is_active OR password_hash IS NOT NULL);
CREATE TABLE auth_sessions(
    token_digest varchar(64) PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    auth_version bigint NOT NULL,
    issued_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    CONSTRAINT auth_sessions_version_positive CHECK(auth_version >= 1),
    CONSTRAINT auth_sessions_expiry_order CHECK(expires_at > issued_at),
    CONSTRAINT auth_sessions_digest_format CHECK(token_digest ~ '^[0-9a-f]{64}$')
);
CREATE INDEX auth_sessions_user_id_idx ON auth_sessions(user_id);
CREATE INDEX auth_sessions_expires_at_idx ON auth_sessions(expires_at);
