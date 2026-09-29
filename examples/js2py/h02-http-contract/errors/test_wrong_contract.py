"""Intentional failing test. Run explicitly; excluded from the default suite."""
from contract_examples import read_case


def test_wrong_assumption_that_delete_returns_json():
    response = read_case("delete-ok")["response"]
    assert response["status"] == 200, "204 is success without a JSON response body"
