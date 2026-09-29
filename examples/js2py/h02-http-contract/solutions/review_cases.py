"""Independent core-contract previews, NOT request validation or persistence."""
from contract_examples import preview_page


def proposed_changes(original: dict, changes: dict) -> dict:
    """Illustrate supplied keys after validation; do not use truthiness filtering."""
    result = original.copy()
    for key in ("title", "minutes", "done", "note"):
        if key in changes:
            result[key] = changes[key]
    return result


def second_page(tasks: list[dict]) -> dict:
    return preview_page(tasks, offset=1, limit=1)
