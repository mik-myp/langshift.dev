"""Real data + statistics + JSON EXPLAIN; no forced planner settings."""
import json
import os
from pathlib import Path
from sqlalchemy import text
from db import make_engine
from migrate import upgrade

QUERY = """SELECT id, title FROM tasks
           WHERE project_id = :project AND status = 'doing'
           ORDER BY id LIMIT 20"""
INDEX = "ix_tasks_project_status_id"


def nodes(plan):
    yield plan
    for child in plan.get("Plans", []):
        yield from nodes(child)


def measure(connection, project):
    rows = connection.execute(text(QUERY), {"project": project}).all()
    document = connection.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + QUERY),
                                  {"project": project}).scalar_one()[0]
    return rows, document


def experiment(engine):
    with engine.begin() as connection:
        user = connection.execute(text("INSERT INTO users(login) VALUES ('planner') RETURNING id")).scalar_one()
        projects = list(connection.execute(text("""
            INSERT INTO projects(name, created_by)
            SELECT 'Project ' || g, :u FROM generate_series(1, 200) AS g RETURNING id
        """), {"u": user}).scalars())
        # Every project receives 300 rows; 30 'doing'. Long-ish descriptions
        # make scanning the table nontrivial. Identity values need not start at 1.
        connection.execute(text("""
            INSERT INTO tasks(project_id, created_by, title, description, status, minutes)
            SELECT (:ids)[1 + ((g-1) % 200)], :u, 'Task ' || g, repeat('context ', 16),
                   CASE WHEN ((g-1)/200) % 10 = 0 THEN 'doing' ELSE 'todo' END, 30
            FROM generate_series(1, 60000) AS g
        """), {"ids": projects, "u": user})
        connection.execute(text("ANALYZE tasks"))
    with engine.connect() as connection:
        before_rows, before = measure(connection, projects[-1])
    with engine.begin() as connection:
        connection.execute(text(f"CREATE INDEX {INDEX} ON tasks (project_id, status, id)"))
        connection.execute(text("ANALYZE tasks"))
    with engine.connect() as connection:
        after_rows, after = measure(connection, projects[-1])
        assert connection.scalar(text("SELECT count(*) FROM tasks")) == 60000
    assert before_rows == after_rows and len(after_rows) == 20
    assert not any(node.get("Index Name") == INDEX for node in nodes(before["Plan"]))
    assert any(node.get("Index Name") == INDEX for node in nodes(after["Plan"]))
    report = {"rows_seeded": 60000, "projects": 200, "returned": len(after_rows),
              "before": before, "after": after,
              "note": "Observed plan only; no exact cost or wall-time performance contract"}
    print("plan before:", [(node["Node Type"], node.get("Index Name")) for node in nodes(before["Plan"])])
    print("plan after:", [(node["Node Type"], node.get("Index Name")) for node in nodes(after["Plan"])])
    print("same result rows:", len(after_rows))
    if os.environ.get("LAB_PLAN_EVIDENCE"):
        Path(os.environ["LAB_PLAN_EVIDENCE"]).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    upgrade()
    engine = make_engine()
    try:
        experiment(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
