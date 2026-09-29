#!/usr/bin/env python3
"""Syntax/source parity checks; deliberately not a claim of full runtime coverage."""

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "content/docs/js2py"
FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.M | re.S)


def python_blocks(text):
    for match in FENCE.finditer(text):
        metadata = match.group(1).strip().split()
        if metadata and metadata[0] in ("python", "py"):
            yield text[: match.start()].count("\n") + 2, match.group(2), metadata


def syntax_errors(text, filename):
    errors = []
    for line, code, metadata in python_blocks(text):
        expected = "expected-error=SyntaxError" in metadata
        # Explicitly labelled editing fragments are checked in their declared
        # syntactic context, never silently skipped or executed as programs.
        class_body = "fragment=class-body" in metadata
        checked_code = "class _LessonFragment:\n" + code if class_body else code
        try:
            compile(
                checked_code,
                "<lesson-snippet>",
                "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
        except SyntaxError as exc:
            if not expected:
                errors.append(
                    f"{filename}:{line + (exc.lineno or 1) - 1 - int(class_body)}: {exc.msg}"
                )
        else:
            if expected:
                errors.append(
                    f"{filename}:{line}: expected SyntaxError but snippet compiles"
                )
    return errors


def run_typing_snippets(paths):
    """Selected declaration-only examples, each in a new bounded Python process.

    This is process isolation for repeatability, not a security sandbox. Do not
    expand it to arbitrary server/database examples without an explicit runner.
    """
    errors = []
    count = 0
    with tempfile.TemporaryDirectory(prefix="js2py-typing-") as directory:
        for path in paths:
            for line, code, metadata in python_blocks(path.read_text(encoding="utf-8")):
                if "smoke=typing" not in metadata:
                    continue
                count += 1
                try:
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", code],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                except subprocess.TimeoutExpired:
                    errors.append(
                        f"{path.name}:{line}: declaration smoke test timed out"
                    )
                    continue
                if result.returncode:
                    errors.append(f"{path.name}:{line}: {result.stderr.strip()}")
    return count, errors


def source_parity_errors(texts, names, lesson):
    """Keep three locales on the same source, executable snippets, and output."""
    errors = []
    references = []
    comparison_code = []
    for filename, text in texts.items():
        refs = re.findall(rf"{re.escape(lesson['loader'])}\('([^']+)'\)", text)
        references.append(refs)
        comparison_code.append(
            [
                (match.group(1), match.group(2))
                for match in FENCE.finditer(text)
                if match.group(1).split()
                and match.group(1).split()[0]
                in (
                    "python",
                    "py",
                    "javascript",
                    "bash",
                    "sh",
                    "shell",
                    "powershell",
                    "sql",
                    "http",
                    "json",
                    "toml",
                    "ini",
                    "yaml",
                    "yml",
                    "dockerfile",
                )
                + (("text",) if lesson.get("compare_text", False) else ())
            ]
        )
        for name in refs:
            if name not in names:
                errors.append(f"{filename}: unknown example {name}")
        if lesson["download"] not in text:
            errors.append(f"{filename}: missing lesson download")
        if any(fragment in text for fragment in lesson["forbidden"]):
            errors.append(f"{filename}: future engineering material in beginner lesson")
        if refs != lesson["refs"]:
            errors.append(f"{filename}: missing or unexpected shared source references")
    if len(references) != 3 or any(ref != references[0] for ref in references[1:]):
        errors.append(f"{lesson['loader']}: three-locale shared source parity failed")
    if comparison_code and any(
        code != comparison_code[0] for code in comparison_code[1:]
    ):
        errors.append(f"{lesson['loader']}: translated code/output fences differ")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-typing", action="store_true")
    args = parser.parse_args()
    errors = []
    files = sorted(COURSE.glob("*.mdx"))
    blocks = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        errors.extend(syntax_errors(text, path.name))
        blocks += sum(1 for _ in python_blocks(text))

    labs = {
        "u11-typing": "u11-typing-files.json",
        "u12-models": "u12-models-files.json",
        "u13-decorators": "u13-decorators-files.json",
        "u14-resources": "u14-resources-files.json",
        "u08-environments": "u08-environments-files.json",
        "u09-testing": "u09-testing-files.json",
        "u10-local-project": "u10-local-project-files.json",
        "u07-files": "u07-files-files.json",
        "u06-modules": "u06-modules-files.json",
        "u00-environment": "u00-files.json",
        "u00-first-script": "u00-first-script-files.json",
        "u01-scalars": "u01-scalars-files.json",
        "u02-containers": "u02-containers-files.json",
        "u03-control-flow": "u03-control-flow-files.json",
        "u04-functions": "u04-functions-files.json",
        "u05-exceptions": "u05-exceptions-files.json",
    }
    backend_rows = json.loads(
        (ROOT / "scripts/tests/fixtures/js2py-backend-chapters.json").read_text()
    )
    labs.update({row["lab"]: row["lab"] + "-files.json" for row in backend_rows})
    for lab, manifest in labs.items():
        for name in json.loads((ROOT / "examples/js2py" / manifest).read_text()):
            path = ROOT / "examples/js2py" / lab / name
            if not path.is_file():
                errors.append(f"Missing shared example: {lab}/{name}")
            elif path.suffix == ".py":
                try:
                    compile(path.read_text(encoding="utf-8"), str(path), "exec")
                except SyntaxError as exc:
                    errors.append(str(exc))

    lessons = [
        {
            "glob": "module-08-projects*.mdx",
            "loader": "getEnvironmentExample",
            "compare_text": True,
            "manifest": "u08-environments-files.json",
            "refs": [
                ".python-version",
                "pyproject.toml",
                "probe.py",
                "app.py",
                "uv.lock",
                "exercises/missing-declaration/pyproject.toml",
                "exercises/missing-declaration/app.py",
                "errors/humanize.py",
                "errors/show_shadow.py",
                "solutions/size-report/pyproject.toml",
                "solutions/size-report/.python-version",
                "solutions/size-report/report.py",
            ],
            "download": "/learning-assets/js2py/u08-environments.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-09-advanced-topics*.mdx",
            "loader": "getTestingExample",
            "compare_text": True,
            "manifest": "u09-testing-files.json",
            "refs": [
                "study.py",
                "first_check.py",
                "wrong_check.py",
                "pyproject.toml",
                "tests/test_study.py",
                "errors/test_false_green.py",
                "errors/test_wrong_expectation.py",
                "errors/not_discovered/check_totals.py",
                "errors/test_import_failure.py",
                "exercises/broken_study.py",
                "exercises/test_broken_study.py",
                "solutions/budget/budget.py",
                "solutions/budget/tests/test_budget.py",
            ],
            "download": "/learning-assets/js2py/u09-testing.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-10-common-pitfalls*.mdx",
            "loader": "getProjectExample",
            "compare_text": True,
            "manifest": "u10-local-project-files.json",
            "refs": [
                "fixtures/initial.json",
                "pyproject.toml",
                ".python-version",
                "demo_resource.py",
                "task_app/__init__.py",
                "task_app/validation.py",
                "task_app/rules.py",
                "task_app/storage.py",
                "task_app/app.py",
                "check_import.py",
                "run_tasks.py",
                "tests/test_rules.py",
                "tests/test_storage.py",
                "fixtures/broken.json",
                "fixtures/wrong-shape.json",
                "solutions/new_requirement.py",
                "solutions/test_new_requirement.py",
            ],
            "download": "/learning-assets/js2py/u10-local-project.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-07-data-automation*.mdx",
            "loader": "getFileExample",
            "compare_text": True,
            "manifest": "u07-files-files.json",
            "refs": [
                "paths.py",
                "read_text.py",
                "read_cursor.py",
                "read_lines.py",
                "encoding_bytes.py",
                "read_binary.py",
                "error_wrong_encoding.py",
                "write_text.py",
                "write_modes.py",
                "create_once.py",
                "closed_stream.py",
                "cleanup_paths.py",
                "pitfall_truncate.py",
                "error_missing_file.py",
                "error_missing_parent.py",
                "error_directory.py",
                "json_values.py",
                "json_limits.py",
                "json_file.py",
                "pitfall_two_documents.py",
                "serialize_before_open.py",
                "fixtures/tasks.json",
                "validate_data.py",
                "inspect_documents.py",
                "exercises/unsafe_load.py",
                "solutions/recover_missing_only.py",
                "solutions/independent/task_store/__init__.py",
                "solutions/independent/task_store/validation.py",
                "solutions/independent/task_store/storage.py",
                "solutions/independent/task_store/app.py",
                "solutions/independent/check_import.py",
                "solutions/independent/run_store.py",
            ],
            "download": "/learning-assets/js2py/u07-files.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-06-web-development*.mdx",
            "loader": "getModuleExample",
            "compare_text": True,
            "manifest": "u06-modules-files.json",
            "refs": [
                "standard_library.py",
                "first_import/task_rules.py",
                "first_import/report.py",
                "first_import/import_styles.py",
                "first_import/missing_name.py",
                "first_import/import_twice.py",
                "bindings/settings.py",
                "bindings/observe.py",
                "entry_points/noisy_report.py",
                "entry_points/use_noisy.py",
                "entry_points/quiet_report.py",
                "entry_points/use_quiet.py",
                "locations/show_context.py",
                "package_demo/task_tools/__init__.py",
                "package_demo/task_tools/rules.py",
                "package_demo/task_tools/report.py",
                "package_demo/task_tools/app.py",
                "package_demo/check_import.py",
                "missing_module.py",
                "first_import/missing_export.py",
                "shadowing/statistics.py",
                "shadowing/show_source.py",
                "cycles/run.py",
                "cycles/cycle_a.py",
                "cycles/cycle_b.py",
                "cycle_fixed/rules.py",
                "cycle_fixed/formatting.py",
                "cycle_fixed/run.py",
                "exercises/noisy_rules.py",
                "exercises/check_noisy.py",
                "solutions/fix_entry.py",
                "solutions/check_fixed_entry.py",
                "solutions/independent/study_plan/__init__.py",
                "solutions/independent/study_plan/rules.py",
                "solutions/independent/study_plan/summary.py",
                "solutions/independent/study_plan/app.py",
                "solutions/independent/check_import.py",
            ],
            "download": "/learning-assets/js2py/u06-modules.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-05-quality-testing-typing*.mdx",
            "loader": "getExceptionExample",
            "compare_text": True,
            "manifest": "u05-exceptions-files.json",
            "refs": [
                "errors/traceback_chain.py",
                "errors/debug_observation.py",
                "debug_fixed.py",
                "debug_logic.py",
                "recover_value.py",
                "errors/unexpected_type.py",
                "validate_minutes.py",
                "errors/negative_minutes.py",
                "handler_order.py",
                "pitfalls/wide_try.py",
                "errors/narrow_try.py",
                "errors/reraise.py",
                "errors/chained_error.py",
                "finally_paths.py",
                "errors/finally_unhandled.py",
                "pitfalls/finally_return.py",
                "pitfalls/partial_mutation.py",
                "apply_estimate.py",
                "assert_invariant.py",
                "pitfalls/assert_validation.py",
                "solutions/fix_boundary.py",
                "solutions/import_report.py",
            ],
            "download": "/learning-assets/js2py/u05-exceptions.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-04-async-programming*.mdx",
            "loader": "getFunctionExample",
            "compare_text": True,
            "manifest": "u04-functions-files.json",
            "refs": [
                "definition_and_call.py",
                "errors/before_definition.py",
                "return_paths.py",
                "errors/printed_result.py",
                "arguments.py",
                "errors/missing_argument.py",
                "errors/duplicate_argument.py",
                "errors/unknown_keyword.py",
                "keyword_only.py",
                "errors/positional_option.py",
                "argument_binding.py",
                "default_values.py",
                "pitfalls/shared_default.py",
                "fresh_defaults.py",
                "local_scope.py",
                "errors/local_before_binding.py",
                "function_values.py",
                "errors/not_callable.py",
                "closure_factory.py",
                "closure_binding.py",
                "task_rules.py",
                "solutions/fix_return.py",
                "solutions/study_rules.py",
            ],
            "download": "/learning-assets/js2py/u04-functions.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-03-oop-functional*.mdx",
            "loader": "getControlFlowExample",
            "compare_text": True,
            "manifest": "u03-control-flow-files.json",
            "refs": [
                "branches.py",
                "truthiness.py",
                "logical.py",
                "for_tasks.py",
                "loop_binding.py",
                "errors/empty_loop.py",
                "ranges.py",
                "errors/zero_step.py",
                "unpacking.py",
                "errors/unpack_pair.py",
                "numbered_tasks.py",
                "dict_iteration.py",
                "while_budget.py",
                "loop_controls.py",
                "pitfalls/mutation_skip.py",
                "safe_filter.py",
                "comprehensions.py",
                "task_summary.py",
                "solutions/fix_total.py",
                "solutions/study_queue.py",
            ],
            "download": "/learning-assets/js2py/u03-control-flow.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-00-python-introduction*.mdx",
            "loader": "getFirstScriptExample",
            "manifest": "u00-first-script-files.json",
            "refs": ["first_steps.py", "solutions/about_me.py"],
            "download": "/learning-assets/js2py/u00-first-script.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-01-syntax-comparison*.mdx",
            "loader": "getScalarExample",
            "compare_text": True,
            "manifest": "u01-scalars-files.json",
            "refs": [
                "bindings.py",
                "scalar_types.py",
                "numbers.py",
                "boolean_none.py",
                "strings.py",
                "conversions.py",
                "errors/text_plus_number.py",
                "errors/invalid_integer.py",
                "formatting.py",
                "task_estimate.py",
                "solutions/fix_minutes.py",
                "solutions/reading_plan.py",
            ],
            "download": "/learning-assets/js2py/u01-scalars.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
        {
            "glob": "module-02-module-system*.mdx",
            "loader": "getContainerExample",
            "compare_text": True,
            "manifest": "u02-containers-files.json",
            "refs": [
                "lists.py",
                "errors/append_rebind.py",
                "errors/list_index.py",
                "dictionaries.py",
                "errors/missing_key.py",
                "missing_values.py",
                "aliases.py",
                "list_copy.py",
                "shallow_copy.py",
                "isolated_copy.py",
                "repeated_rows.py",
                "tuples.py",
                "errors/tuple_assignment.py",
                "sets.py",
                "errors/unhashable_member.py",
                "task_board.py",
                "solutions/fix_draft.py",
                "solutions/study_board.py",
            ],
            "download": "/learning-assets/js2py/u02-containers.zip",
            "forbidden": ["getU00Example(", "/u00-environment.zip"],
        },
    ]
    transition_rows = json.loads(
        (ROOT / "scripts/tests/fixtures/js2py-transition-foundations.json").read_text()
    )
    lessons.extend(
        {
            "glob": row["slug"] + "*.mdx",
            "loader": row["loader"],
            "compare_text": True,
            "manifest": row["lab"] + "-files.json",
            "refs": row["refs"],
            "download": "/learning-assets/js2py/" + row["lab"] + ".zip",
            "forbidden": [],
        }
        for row in transition_rows + backend_rows
    )
    for lesson in lessons:
        names = json.loads((ROOT / "examples/js2py" / lesson["manifest"]).read_text())
        texts = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(COURSE.glob(lesson["glob"]))
        }
        errors.extend(source_parity_errors(texts, names, lesson))

    if args.smoke_typing:
        count, smoke_errors = run_typing_snippets(
            sorted(COURSE.glob("module-11-pythonic-code*.mdx"))
        )
        errors.extend(smoke_errors)
        print(f"Typing declaration smoke checks: {count} fresh processes")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(
        f"js2py content OK: {len(files)} MDX files, {blocks} Python fences; L00–L14 and {len(backend_rows)} registered backend chapters source parity OK"
    )
    print(
        "Scope: syntax + selected declarations, not all examples or static type correctness"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
