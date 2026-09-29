from solutions.check_matrix import compatible

def test_backward_application_compatibility():
    assert compatible("v1","006_task_operations")
    assert compatible("v1","007_project_description")
    assert compatible("v2","007_project_description")
    assert not compatible("v2","006_task_operations")
    assert not compatible("v3","007_project_description")
    assert not compatible("v1","unknown")


def test_preflight_reads_real_migration_state():
    import pytest
    from ops.cluster import OwnedCluster
    from ops.data import grant_app
    from ops.migrate import upgrade
    from solutions.preflight import check_release

    with OwnedCluster() as cluster:
        upgrade(cluster.root, "006_task_operations")
        grant_app(cluster.root)
        with pytest.raises(ValueError):
            check_release(cluster.root, "v2")
        upgrade(cluster.root, "007_project_description")
        assert check_release(cluster.root, "v1") == "007_project_description"
        assert check_release(cluster.root, "v2") == "007_project_description"
        with pytest.raises(ValueError):
            check_release(cluster.root, "unknown")
