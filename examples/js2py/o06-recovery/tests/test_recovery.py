import pytest
from ops.backup import backup,restore,fingerprint
from ops.cluster import OwnedCluster
from ops.data import seed
from ops.migrate import upgrade
from ops.recover import constraint_checks


def test_actual_restore_and_constraints():
    with OwnedCluster() as cluster:
        upgrade(cluster.root,"007_project_description");seed(cluster.root)
        archive,manifest=backup(cluster)
        restore(cluster,archive,manifest)
        assert fingerprint(cluster.root,"restored")==manifest["tables"]
        constraint_checks(cluster.root,"restored")


def test_checksum_failure_does_not_create_target():
    with OwnedCluster() as cluster:
        upgrade(cluster.root,"007_project_description");seed(cluster.root)
        archive,manifest=backup(cluster)
        archive.write_bytes(b"not a PostgreSQL archive")
        with pytest.raises(ValueError):restore(cluster,archive,manifest)
        assert "restored" not in cluster.databases


def test_restore_never_overwrites_an_existing_target():
    with OwnedCluster() as cluster:
        upgrade(cluster.root,"007_project_description");seed(cluster.root)
        archive,manifest=backup(cluster);cluster.create_database("restored")
        with pytest.raises(RuntimeError):restore(cluster,archive,manifest)
