from ops.cluster import connect
from solutions.check_matrix import compatible


def check_release(root, release, database="source"):
    with connect(root, database, "lab_app") as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    if not compatible(release, revision):
        raise ValueError("Release/schema pair is not approved; do not start workers")
    return revision
