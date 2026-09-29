from copy import deepcopy
import json

import pytest

from contract_examples import CASE_NAMES, ROOT, check_example, preview_page, read_case


@pytest.mark.parametrize("name", CASE_NAMES)
def test_each_proposed_exchange_is_self_consistent(name):
    check_example(read_case(name))


@pytest.mark.parametrize("name,offset,limit", [
    ("list-first", 0, 2), ("list-last", 2, 2),
    ("list-empty", 99, 2), ("list-default", 0, 20),
])
def test_pagination_matches_the_core_contract(name, offset, limit):
    tasks = json.loads((ROOT / "fixtures/tasks.json").read_text(encoding="utf-8"))
    reversed_tasks = list(reversed(tasks))
    original = deepcopy(reversed_tasks)
    assert preview_page(reversed_tasks, offset, limit) == read_case(name)["response"]["body"]
    assert reversed_tasks == original


@pytest.mark.parametrize("offset,limit", [(-1, 2), (0, 0), (0, 101), (True, 2), (0, True), ("0", 2)])
def test_preview_rejects_invalid_already_parsed_values(offset, limit):
    with pytest.raises(ValueError):
        preview_page([], offset, limit)


def test_limit_100_is_allowed_without_next_offset():
    assert preview_page([], limit=100) == {"items": [], "limit": 100, "offset": 0, "total": 0}


def test_204_is_not_the_json_value_null():
    example = read_case("delete-ok")
    example["response"]["body"] = {"ok": True}
    with pytest.raises(ValueError, match="204"):
        check_example(example)


def test_creation_does_not_strip_a_valid_title():
    example = read_case("create-ok")
    assert example["response"]["body"]["title"] == "  Ship the draft  "
    example["response"]["body"]["title"] = "Ship the draft"
    with pytest.raises(ValueError, match="preserves"):
        check_example(example)


def test_old_custom_error_envelope_is_rejected():
    example = read_case("blank-title")
    example["response"]["body"] = {"error": {"code": "validation_error"}}
    with pytest.raises(ValueError, match="detail"):
        check_example(example)


def test_internal_fields_are_not_public():
    example = read_case("get-task")
    example["response"]["body"]["internal_tag"] = "must-not-leak"
    with pytest.raises(ValueError, match="public task fields"):
        check_example(example)


def test_malformed_json_matches_fastapi_422_not_an_invented_400():
    example = read_case("malformed-json")
    assert example["response"]["status"] == 422
    assert example["response"]["body"]["detail"][0]["type"] == "json_invalid"


def test_omitted_note_is_preserved_and_explicit_null_clears():
    assert read_case("patch-omit-note")["response"]["body"]["note"] == "keep me"
    assert read_case("patch-clear-note")["response"]["body"]["note"] is None


def test_empty_patch_and_explicit_zero_false_have_distinct_effects():
    unchanged = read_case("empty-patch")["response"]["body"]
    changed = read_case("patch-zero-false")["response"]["body"]
    assert unchanged["minutes"] == 25
    assert changed["minutes"] == 0 and changed["done"] is False


def test_reading_a_delete_example_does_not_delete_a_task():
    before = read_case("get-task")
    read_case("delete-ok")
    assert read_case("get-task") == before
