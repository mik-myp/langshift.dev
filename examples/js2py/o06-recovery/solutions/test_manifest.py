import pytest
from solutions.check_manifest import REQUIRED,verify_manifest

def test_missing_security_tables_cannot_pass():
    manifest={"created_at":100,"tables":{name:{} for name in REQUIRED},"bytes":1}
    assert verify_manifest(manifest,110,10)
    with pytest.raises(ValueError):verify_manifest(manifest,111,10)
    with pytest.raises(ValueError):verify_manifest(manifest,99,10)
    with pytest.raises(ValueError):verify_manifest(manifest,110,float("nan"))
    with pytest.raises(ValueError):verify_manifest(manifest,float("inf"),10)
    del manifest["tables"]["auth_sessions"]
    with pytest.raises(ValueError):verify_manifest(manifest,110,10)
