def compatible(release: str, revision: str) -> bool:
    matrix={"v1":{"006_task_operations","007_project_description"},"v2":{"007_project_description"}}
    return revision in matrix.get(release,set())
