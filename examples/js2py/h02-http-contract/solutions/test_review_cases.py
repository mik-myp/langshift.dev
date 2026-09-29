import json
from contract_examples import ROOT, check_example, preview_page
from solutions.review_cases import proposed_changes, second_page


def test_order_count_and_slice():
    tasks = json.loads((ROOT / "fixtures/tasks.json").read_text(encoding="utf-8"))
    page = second_page(list(reversed(tasks)))
    assert [task["id"] for task in page["items"]] == [2]
    assert page == {"items": [tasks[1]], "limit": 1, "offset": 1, "total": 3}


def test_past_end_is_an_empty_page_not_a_missing_resource():
    assert preview_page([], 5, 2) == {"items": [], "limit": 2, "offset": 5, "total": 0}


def test_omitted_note_is_preserved():
    original = {"title": "Original", "minutes": 25, "done": True, "note": "keep me"}
    result = proposed_changes(original, {"title": "Changed"})
    assert result["note"] == "keep me"
    assert original["title"] == "Original"


def test_explicit_null_zero_and_false_are_not_dropped():
    original = {"title": "Original", "minutes": 25, "done": True, "note": "keep me"}
    result = proposed_changes(original, {"note": None, "minutes": 0, "done": False})
    assert result == {"title": "Original", "minutes": 0, "done": False, "note": None}
    assert original["note"] == "keep me"


def test_six_complete_exchanges_match_the_preview():
    examples = json.loads((ROOT / "solutions/exchanges.json").read_text(encoding="utf-8"))
    assert len(examples) == 6
    for example in examples:
        check_example(example)
    tasks = json.loads((ROOT / "fixtures/tasks.json").read_text(encoding="utf-8"))
    assert examples[0]["response"]["body"] == second_page(tasks)
    assert examples[1]["response"]["body"] == preview_page(tasks, 99, 2)
    for example in examples[2:4]:
        assert example["response"]["body"] == proposed_changes(tasks[0], example["request"]["body"])
    assert [e["response"]["status"] for e in examples[4:]] == [422, 422]
