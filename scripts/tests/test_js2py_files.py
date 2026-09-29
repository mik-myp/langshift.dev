"""L07: real file bytes, resource lifetime, layered failures and independent transfer."""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "examples/js2py/u07-files"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
NAMES = json.loads((ROOT / "examples/js2py/u07-files-files.json").read_text())
FIXTURES = json.loads((Path(__file__).parent / "fixtures/js2py-files.json").read_text())
CASES = FIXTURES["cases"]
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-07-data-automation*.mdx"))


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.pop("VIRTUAL_ENV", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def execute(lab, args, cwd=".", prefix=None):
    return subprocess.run(
        (prefix or [PYTHON]) + args,
        cwd=lab / cwd,
        env=environment(),
        text=True,
        capture_output=True,
        timeout=120,
    )


def normalized(text, lab):
    text = text.replace(str(lab.resolve()), "<LAB>").replace(str(lab), "<LAB>")
    # Normalize only path-display lines, never repr's significant backslashes.
    return "\n".join(
        line.replace("\\", "/")
        if line.startswith(("Cwd:", "Relative:", "Target:"))
        else line
        for line in text.split("\n")
    )


def assert_case(test, lab, case, prefix=None):
    result = execute(lab, case["args"], case["cwd"], prefix)
    test.assertEqual(normalized(result.stdout, lab), case["stdout"], case["id"])
    if "errors" in case:
        test.assertNotEqual(result.returncode, 0, case["id"])
        last = result.stderr.splitlines()[-1]
        test.assertTrue(any(error + ":" in last for error in case["errors"]), last)
        for fragment in case.get("stderr_contains", []):
            test.assertIn(fragment, result.stderr, case["id"])
    else:
        test.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if prefix is None:
            test.assertEqual(result.stderr, "")
    return result


def verify_tree(test, lab):
    for name in NAMES:
        test.assertEqual((lab / name).read_bytes(), (LAB / name).read_bytes(), name)
    for name, text in FIXTURES["outputs"].items():
        test.assertEqual((lab / name).read_bytes(), text.encode("utf-8"), name)
    expected = set(NAMES) | set(FIXTURES["outputs"])
    for path in lab.rglob("*"):
        test.assertFalse(path.is_symlink(), str(path))
        test.assertNotEqual(path.name, ".venv")
        if path.is_file() and str(path.relative_to(lab)) not in expected:
            test.assertEqual(path.parent.name, "__pycache__", str(path))
            test.assertEqual(path.suffix, ".pyc", str(path))
            source = path.parent.parent / (path.name.split(".", 1)[0] + ".py")
            test.assertIn(str(source.relative_to(lab)), NAMES)
    test.assertFalse((lab / "_output/absent-folder").exists())


class FileChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="js2py-files-test-")
        self.addCleanup(self.temp.cleanup)
        self.lab = Path(self.temp.name).resolve() / "u07-files"
        for name in NAMES:
            path = self.lab / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((LAB / name).read_bytes())

    def check_program(self, source, cwd="solutions/independent"):
        result = execute(self.lab, ["-c", textwrap.dedent(source)], cwd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_all_documented_commands_first_repeated_and_generated_bytes(self):
        self.assertEqual(len(CASES), 33)
        self.assertEqual(sum("errors" in c for c in CASES), 8)
        for case in CASES:
            with self.subTest(case=case["id"]):
                assert_case(self, self.lab, case)
        verify_tree(self, self.lab)
        self.assertEqual(len((self.lab / "_output/note.txt").read_bytes()), 14)

    def test_three_locale_source_fence_output_and_unicode_literal_parity(self):
        refs, fences = [], []
        for lesson in LESSONS:
            text = lesson.read_text()
            refs.append(re.findall(r"getFileExample\('([^']+)'\)", text))
            fences.append(
                re.findall(
                    r"```(?:python|javascript|bash|text|json)[^\n]*\n(.*?)```",
                    text,
                    re.S,
                )
            )
            self.assertEqual(text.count("<details>"), 3)
            self.assertNotIn("<details open", text)
            self.assertIn("/learning-assets/js2py/u07-files.zip", text)
            self.assertIn("compare={true} canRun={false}", text)
            self.assertEqual(len(re.findall(r"^## \d+\.", text, re.M)), 15)
            self.assertIn("L08", text)
            self.assertNotIn("getU00Example(", text)
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0], refs[1])
        self.assertEqual(refs[1], refs[2])
        self.assertEqual(fences[0], fences[1])
        self.assertEqual(fences[1], fences[2])
        expected = {n for n in NAMES if n.endswith(".py")} | {"fixtures/tasks.json"}
        self.assertEqual(set(refs[0]), expected)
        self.assertEqual(len(refs[0]), 32)
        # Full output blocks are actual independently asserted command results.
        outputs = {c["stdout"].strip() for c in CASES if c["stdout"]}
        for text in fences[0]:
            if text.startswith(
                (
                    "Inside closed:",
                    "First:",
                    "Text length:",
                    "Mode: normal",
                    "Is text:",
                    "Restored:",
                    "tasks.json:",
                    "Source: ",
                )
            ):
                self.assertIn(text.strip(), outputs)

    def test_sources_use_current_stage_not_custom_context_managers_or_frameworks(self):
        self.assertEqual(sum(n.endswith(".py") for n in NAMES), 31)
        for name in NAMES:
            if not name.endswith(".py"):
                continue
            tree = ast.parse((LAB / name).read_text())
            for node in ast.walk(tree):
                self.assertNotIsInstance(
                    node,
                    (
                        ast.ClassDef,
                        ast.AsyncFunctionDef,
                        ast.Await,
                        ast.Yield,
                        ast.YieldFrom,
                        ast.AsyncWith,
                        ast.AnnAssign,
                    ),
                    name,
                )
                if isinstance(node, ast.FunctionDef):
                    self.assertFalse(node.decorator_list, name)
                    self.assertIsNone(node.returns, name)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"eval", "exec", "__import__"}, name)

    def test_utf8_fixture_characters_bytes_cursors_and_default_newline_translation(
        self,
    ):
        self.assertEqual(
            (self.lab / "fixtures/notes.txt").read_bytes(),
            "Python 学习\n  keep spaces  \n".encode(),
        )
        self.assertEqual((self.lab / "fixtures/invalid-utf8.bin").read_bytes(), b"\xff")
        self.check_program("""
            from pathlib import Path
            directory = Path("scratch")
            directory.mkdir()
            path = directory / "line-endings.txt"
            path.write_bytes(b"A\\r\\nB\\rC\\n")
            with path.open("r", encoding="utf-8") as stream:
                assert stream.read() == "A\\nB\\nC\\n"
            with path.open("rb") as stream:
                assert stream.read() == b"A\\r\\nB\\rC\\n"
            with path.open("w", encoding="utf-8", newline="\\n") as stream:
                assert stream.write("学习\\n") == 3
            assert path.read_bytes() == "学习\\n".encode("utf-8")
        """)

    def test_exclusive_creation_preserves_existing_bytes(self):
        first = next(c for c in CASES if c["id"] == "create-first")
        second = next(c for c in CASES if c["id"] == "create-again")
        assert_case(self, self.lab, first)
        path = self.lab / "_output/once.txt"
        path.write_bytes(b"important existing scratch bytes\x00")
        before = path.read_bytes()
        assert_case(self, self.lab, second)
        self.assertEqual(path.read_bytes(), before)

    def test_import_does_not_create_directories_or_read_or_write_data(self):
        output = self.check_program("""
            from pathlib import Path
            from unittest.mock import patch
            with patch.object(Path, "open", side_effect=AssertionError("unexpected file open")), patch.object(Path, "mkdir", side_effect=AssertionError("unexpected mkdir")):
                import task_store.app
                import task_store.storage
                import task_store.validation
                import run_store
            assert not Path("_output").exists()
        """)
        self.assertEqual(output, "")
        self.assertEqual(
            self.check_program(
                "import validate_data; import serialize_before_open", "."
            ),
            "",
        )
        self.assertFalse((self.lab / "_output").exists())
        self.assertEqual(
            self.check_program("import recover_missing_only", "solutions"), ""
        )
        self.assertEqual(self.check_program("import unsafe_load", "exercises"), "")
        self.assertFalse((self.lab / "exercises/_output").exists())

    def test_main_sentinel_only_runs_for_explicit_entries(self):
        path = self.lab / "solutions/independent/task_store/app.py"
        path.write_text(
            path.read_text().replace(
                "def main():", 'def main():\n    raise RuntimeError("ENTRY_SENTINEL")'
            )
        )
        self.assertEqual(
            self.check_program("import task_store.app; import run_store"), ""
        )
        for args, cwd in [
            (["-m", "task_store.app"], "solutions/independent"),
            (["solutions/independent/run_store.py"], "."),
        ]:
            result = execute(self.lab, args, cwd)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RuntimeError: ENTRY_SENTINEL", result.stderr)
            self.assertEqual(result.stdout, "")
        self.assertFalse((self.lab / "solutions/independent/_output").exists())

    def test_json_comparison_and_default_decoder_limits_are_real(self):
        lesson = LESSONS[0].read_text()
        snippet = re.search(
            r"```python case=json-text-comparison\n(.*?)```", lesson, re.S
        )[1]
        self.assertEqual(
            self.check_program(snippet),
            '{\n  "title": "学习",\n  "done": false\n}\n学习\n',
        )
        self.check_program("""
            import json
            import math
            from task_store.validation import validate_tasks
            assert math.isnan(json.loads("NaN"))
            assert json.loads('{"a": 1, "a": 2}') == {"a": 2}
            repeated = json.loads('[{"title":"A", "minutes":10, "minutes":20, "done":false}]')
            assert validate_tasks(repeated)[0]["minutes"] == 20
            # This explicitly verifies the documented limit, not duplicate detection.
            for token in ["NaN", "Infinity", "-Infinity"]:
                value = json.loads('[{"title":"A", "minutes":' + token + ', "done":false}]')
                try:
                    validate_tasks(value)
                except ValueError:
                    continue
                raise AssertionError("noninteger minutes accepted")
        """)

    def test_validation_matrix_accepts_zero_unicode_duplicates_and_owns_results(self):
        self.check_program("""
            from copy import deepcopy
            from itertools import product, permutations
            from task_store.validation import validate_tasks
            count = 0
            for title, minutes, done in product(["Read", "练习", "  keep  ", "🌱"], [0, 1, 20, 35], [False, True]):
                rows = [{"title": title, "minutes": minutes, "done": done}]
                before = deepcopy(rows)
                first, second = validate_tasks(rows), validate_tasks(rows)
                assert first == rows == before == second
                assert first is not rows and first[0] is not rows[0]
                assert first is not second and first[0] is not second[0]
                first[0]["minutes"] = 99
                first.append({"title": "Extra", "minutes": 0, "done": True})
                assert rows == before == second
                count += 1
            assert count == 32
            one, two = validate_tasks([]), validate_tasks([])
            one.append({"title": "X", "minutes": 0, "done": False})
            assert two == []
            rows = [{"title":"Same", "minutes":n, "done":False} for n in [0,1,2]]
            for order in permutations(rows):
                assert validate_tasks(list(order)) == list(order)
        """)

    def test_invalid_shapes_fields_and_rows_preserve_inputs(self):
        self.check_program("""
            from copy import deepcopy
            from task_store.validation import validate_tasks
            for root in [None, {}, "[]", 0, True, (1,2)]:
                try: validate_tasks(root)
                except ValueError as error: assert "tasks must be a list" in str(error)
                else: raise AssertionError(root)
            good = {"title": "Read", "minutes": 20, "done": False}
            invalid = [None, "row", [], {}, {"title":"A"}, dict(good, extra=1)]
            for field, values in [("title", [None, 1, False, "", " ", "\\t\\n"]), ("minutes", [None, True, False, 20.0, "20", -1, [], float("nan"), float("inf")]), ("done", [None, 0, 1, "false", []])]:
                for value in values:
                    row = dict(good)
                    row[field] = value
                    invalid.append(row)
            for field in good:
                row = dict(good)
                del row[field]
                invalid.append(row)
            for bad in invalid:
                for position in range(3):
                    rows = [dict(good), dict(good)]
                    rows.insert(position, bad)
                    # repr comparison covers NaN without relying on NaN equality.
                    before = repr(rows)
                    try: validate_tasks(rows)
                    except ValueError as error: assert f"task {position+1}" in str(error)
                    else: raise AssertionError(rows)
                    assert repr(rows) == before
        """)

    def test_save_and_fresh_load_preserve_data_format_and_independent_results(self):
        self.check_program("""
            from pathlib import Path
            from copy import deepcopy
            from task_store.storage import load_tasks, save_tasks
            path = Path("saved.json")
            rows = [{"title": "  练习  ", "minutes": 0, "done": False}, {"title": "Read", "minutes": 20, "done": True}]
            before = deepcopy(rows)
            assert save_tasks(path, rows) is None
            raw = path.read_bytes()
            assert raw.endswith(b"\\n") and not raw.endswith(b"\\n\\n")
            assert b"\\r" not in raw and b"\\\\u" not in raw
            assert "练习".encode() in raw and b'"done": false' in raw and b'"done": true' in raw
            assert rows == before
            first, second = load_tasks(path), load_tasks(path)
            first[0]["title"] = "changed"
            first.append({"title":"X", "minutes":0, "done":True})
            assert second == rows == before and path.read_bytes() == raw
            save_tasks(path, [])
            assert path.read_bytes() == b"[]\\n" and load_tasks(path) == []
        """)

    def test_rejected_save_does_not_truncate_or_create_and_preparation_faults_propagate(
        self,
    ):
        self.check_program("""
            from pathlib import Path
            from unittest.mock import patch
            import task_store.storage as store
            existing, absent = Path("existing.json"), Path("absent.json")
            original = b"preserve even a damaged existing file\\x00"
            existing.write_bytes(original)
            bad_values = [None, {}, [None], [{}], [{"title":"A", "minutes":True, "done":False}], [{"title":" ", "minutes":0, "done":False}]]
            for bad in bad_values:
                for path in [existing, absent]:
                    with patch.object(Path, "open", side_effect=AssertionError("opened before validation")):
                        try: store.save_tasks(path, bad)
                        except ValueError: pass
                        else: raise AssertionError("accepted invalid input")
                    assert existing.read_bytes() == original and not absent.exists()
            rows = [{"title":"A", "minutes":1, "done":False}]
            for attribute, error in [("validate_tasks", RuntimeError("validator bug")), ("json.dumps", TypeError("encoder failed"))]:
                target = "task_store.storage." + attribute
                with patch(target, side_effect=error), patch.object(Path, "open", side_effect=AssertionError("opened before preparation")):
                    try: store.save_tasks(existing, rows)
                    except type(error) as caught: assert caught is error
                    else: raise AssertionError("failure hidden")
                assert existing.read_bytes() == original
        """)

    def test_read_failures_and_validation_leave_actual_acquired_streams_closed(self):
        self.check_program("""
            import json
            from pathlib import Path
            from unittest.mock import patch
            from task_store.storage import load_tasks, save_tasks
            path = Path("case.json")
            opened = []
            original_open = Path.open
            def track(self, *args, **kwargs):
                stream = original_open(self, *args, **kwargs)
                opened.append(stream)
                return stream
            cases = [(b"[]", None), (b"{broken", json.JSONDecodeError), (b"\\xff", UnicodeDecodeError), (b"{}", ValueError)]
            for content, kind in cases:
                path.write_bytes(content)
                opened.clear()
                with patch.object(Path, "open", track):
                    try: result = load_tasks(path)
                    except Exception as error:
                        assert kind is not None and isinstance(error, kind)
                    else:
                        assert kind is None and result == []
                assert len(opened) == 1 and opened[0].closed
                assert path.read_bytes() == content
            opened.clear()
            with patch.object(Path, "open", track):
                save_tasks(path, [{"title":"A", "minutes":1, "done":False}])
            assert len(opened) == 1 and opened[0].closed
        """)

    def test_missing_parent_permissions_and_unknown_io_errors_are_not_empty_data(self):
        self.check_program("""
            from pathlib import Path
            from unittest.mock import patch
            from task_store.storage import load_tasks, save_tasks
            path = Path("absent-parent") / "tasks.json"
            for action in [lambda: load_tasks(path), lambda: save_tasks(path, [])]:
                try: action()
                except FileNotFoundError: pass
                else: raise AssertionError("missing parent hidden")
            assert not path.parent.exists()
            for kind in [PermissionError, IsADirectoryError, OSError, RuntimeError, KeyboardInterrupt, SystemExit]:
                marker = kind("injected open failure")
                for action in [lambda: load_tasks(Path("x")), lambda: save_tasks(Path("x"), [])]:
                    with patch.object(Path, "open", side_effect=marker):
                        try: action()
                        except kind as error: assert error is marker
                        else: raise AssertionError("unknown failure hidden")
            assert not Path("x").exists()
        """)

    def test_write_failure_closes_stream_but_is_not_misrepresented_as_atomic(self):
        self.check_program("""
            from pathlib import Path
            from unittest.mock import patch
            from task_store.storage import save_tasks
            path = Path("partial.json")
            path.write_text("original bytes", encoding="utf-8")
            actual_open = Path.open
            opened = []
            class FailingWriter:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def write(self, text):
                    self.stream.write(text[:4])
                    raise OSError("simulated disk failure")
                def __exit__(self, *error):
                    self.stream.close()
                    return False
            def fail(self, *args, **kwargs):
                stream = actual_open(self, *args, **kwargs)
                opened.append(stream)
                return FailingWriter(stream)
            rows = [{"title":"A", "minutes":1, "done":False}]
            with patch.object(Path, "open", fail):
                try: save_tasks(path, rows)
                except OSError as error: assert str(error) == "simulated disk failure"
                else: raise AssertionError("write failure hidden")
            assert opened[0].closed
            assert path.read_bytes() == b"[\\n  "
            assert rows == [{"title":"A", "minutes":1, "done":False}]
        """)

    def test_repair_recovers_only_missing_and_does_not_hide_other_errors(self):
        self.check_program(
            """
            import json
            from pathlib import Path
            from unittest.mock import patch
            import recover_missing_only as fixed
            missing = Path("missing.json")
            assert fixed.load_or_empty(missing) == [] and not missing.exists()
            path = Path("repair-case.json")
            for data, expected in [(b"[]", []), (b"[1]", [1])]:
                path.write_bytes(data)
                assert fixed.load_or_empty(path) == expected
                assert path.read_bytes() == data
            for data, kind in [(b"{broken", json.JSONDecodeError), (b"\\xff", UnicodeDecodeError), (b"{}", ValueError)]:
                path.write_bytes(data)
                try: fixed.load_or_empty(path)
                except kind: pass
                else: raise AssertionError("damaged input treated as empty")
                assert path.read_bytes() == data
            for kind in [PermissionError, OSError, RuntimeError]:
                marker = kind("known test failure")
                with patch.object(Path, "open", side_effect=marker):
                    try: fixed.load_or_empty(path)
                    except kind as error: assert error is marker
                    else: raise AssertionError("failure hidden")
        """,
            "solutions",
        )

    def test_app_repeated_runs_empty_and_changed_inputs_persist_in_fresh_processes(
        self,
    ):
        for identity in ["independent-first", "independent-again", "wrapper-other-cwd"]:
            assert_case(self, self.lab, next(c for c in CASES if c["id"] == identity))
        path = self.lab / "solutions/independent/_output/tasks.json"
        for rows, expected in [
            ([], 0),
            ([{"title": "Zero", "minutes": 0, "done": False}], 0),
            ([{"title": "练习", "minutes": 36, "done": False}], 36),
            ([{"title": "Done", "minutes": 35, "done": True}], 0),
            (
                [
                    {"title": "Read", "minutes": 2, "done": False},
                    {"title": "Read", "minutes": 3, "done": False},
                ],
                0,
            ),
        ]:
            path.write_text(json.dumps(rows), encoding="utf-8")
            result = execute(self.lab, ["solutions/independent/run_store.py"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith("Source: existing file\n"))
            self.assertIn(
                f"Saved: {len(rows)}\nPending minutes: {expected}\n", result.stdout
            )
            stored = json.loads(path.read_text())
            expected_rows = [
                dict(row, done=True) if row["title"] == "Read" else row for row in rows
            ]
            self.assertEqual(stored, expected_rows)
        self.assertFalse((self.lab / "_output").exists())

    def test_app_refuses_corrupt_encoding_syntax_and_schema_without_writing(self):
        output = self.lab / "solutions/independent/_output"
        output.mkdir()
        path = output / "tasks.json"
        for raw, expected, kind in [
            (b"{broken", "Invalid JSON", "JSONDecodeError"),
            (b"\xff", "Invalid UTF-8", "UnicodeDecodeError"),
            (b"{}", "Invalid task data", "ValueError"),
            (
                b'[{"title":"A", "minutes":true, "done":false}]',
                "Invalid task data",
                "ValueError",
            ),
        ]:
            path.write_bytes(raw)
            result = execute(
                self.lab, ["-m", "task_store.app"], "solutions/independent"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, expected + "; file unchanged\n")
            self.assertIn(kind + ":", result.stderr)
            self.assertNotIn("Saved:", result.stdout)
            self.assertEqual(path.read_bytes(), raw)

    def test_independent_reconstruction_outside_download_and_other_cwd(self):
        parent = Path(self.temp.name).resolve() / "from-empty"
        parent.mkdir()
        self.assertEqual(list(parent.iterdir()), [])
        scratch = parent / "my_tasks"
        prefix = "solutions/independent/"
        for name in NAMES:
            if name.startswith(prefix):
                target = scratch / name.removeprefix(prefix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((LAB / name).read_bytes())
        assert_case(
            self,
            scratch,
            dict(next(c for c in CASES if c["id"] == "independent-import"), cwd="."),
        )
        self.assertFalse((scratch / "_output").exists())
        result = execute(parent, ["my_tasks/run_store.py"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((scratch / "_output/tasks.json").is_file())
        self.assertFalse((parent / "_output").exists())
        again = execute(scratch, ["-m", "task_store.app"])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertTrue(again.stdout.startswith("Source: existing file\n"))
        for forbidden in ["pyproject.toml", "uv.lock", ".venv"]:
            self.assertFalse((scratch / forbidden).exists())

    def test_download_exactly_matches_sources_and_binary_fixtures(self):
        self.assertEqual(len(NAMES), 38)
        self.assertEqual(len(NAMES), len(set(NAMES)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u07-files.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {"u07-files/" + name for name in NAMES}
            )
            for name in NAMES:
                self.assertEqual(
                    archive.read("u07-files/" + name), (LAB / name).read_bytes()
                )
                self.assertNotIn("_output", Path(name).parts)
                self.assertNotIn("__pycache__", Path(name).parts)
                self.assertNotIn("..", Path(name).parts)
                self.assertFalse(Path(name).is_absolute())
            self.assertEqual(
                archive.read("u07-files/fixtures/invalid-utf8.bin"), b"\xff"
            )


if __name__ == "__main__":
    unittest.main()
