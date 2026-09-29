# G01 — Independent task-comment requirements and evidence package

Verified 2026-09-28. This is not a reference backend or a suite that validates a student's application. Mainline/human review must establish O06 restoration and controlled-release evidence; missing prerequisites cannot be automatically marked passed here.

## What is delivered

Task comments are an equivalent controlled alternative to the capstone label extension; both are not required. New complexity includes author versus owner permissions, membership removal, versioned editing, nonresurrectable redaction, repeated/uncertain requests, populated upgrades, rollback, restoration and invited feedback. Students choose and defend their model, interface, transaction mechanism, migrations and delivery strategy. Their implementation answers are not supplied.

- requirements.json: machine-readable product contract g01-comments-v1; logical facts are not prescribed physical tables.
- fixtures/actors-and-data.json: synthetic actors, objects and content boundaries; labels are not prescribed IDs or a production import.
- scenarios.json: S01–S24 preconditions/actions/outcomes and hard gates, not an executed backend test suite.
- rubric.json: six human-reviewed dimensions totaling 100, suggested minimum 80, and noncompensable gates.
- templates/evidence.json: unfilled student report with 24 not_run cases and four separate claims.
- templates/fixture-bindings.json: mappings into a student's isolated model, without credentials.
- templates/checkpoint.json: revisions, owned target, established facts, next evidence and stopped resources.
- templates/reviewer-record.json: blank human review without a prefilled graduation or public-operation approval.
- check_evidence.py: optional standard-library-only material-format checker.
- tests/test_materials.py: material/catalog unit tests, not comment API tests.
- sources.json, three READMEs and FILES.json: provenance, execution contract and packaging allowlist.

## Check the package without a backend, but do not infer graduation

Reading JSON/Markdown requires no runtime. Optional tools were tested on Python 3.13.15, recorded in .python-version. There are no external dependencies, so no invented dependency lock and no requirement for uv, pytest, PostgreSQL, Docker or frontend tooling. Use existing Python; install no system service.

Work inside extracted g01-graduation:

```bash
python3 --version
python3 check_evidence.py templates/evidence.json
python3 -m unittest discover -s tests -v
```

Deterministic output for the untouched template:

```text
{"artifact_files_verified": false, "backend_verified": false, "format_valid": true, "graduation_awarded": false, "public_operation_verified": false, "scenario_status_counts": {"blocked": 0, "fail": 0, "not_run": 24, "pass": 0}}
```

Expect 15 material unit tests, with variable duration. Author verification also runs them from an allowlisted ZIP extraction. They cover missing/duplicate cases, invalid references/paths, false timestamps, malformed JSON and synthetic relationships, not a student's backend. All 24 student business scenarios remain not_run.

Exit 0 means acceptable format; invalid material exits 1. The checker does not open artifact files to verify digests, authenticate claims, contact networks/databases, scan all secrets, score work, award graduation or confirm deployment. An in-memory fictional-report test deliberately proves that correct form does not establish a correct backend; it is not an operational record.

## Express evidence without prescribing implementation

Keep the original template blank and put a personal report in a separate submission directory. Executed claims should link code/schema revision, exclusive environment, time, input, response, persistent state and redacted artifact paths. Pass is the submitter's assertion subject to review; fail preserves counterexamples; blocked identifies missing conditions and ownership; not_run must not invent success or timestamps.

Concurrency requires actual overlap. A lost response cannot be replaced by assuming no commit. Recovery means actual restoration into an isolated target. A backup file, empty-database migration, green screenshot, coverage percentage or single final row can each be insufficient. The lesson's three collapsed review sections explain these counterexamples without supplying backend implementation steps.

Relative paths and sha256 fields help locate material, but the format tool does not inspect their content. The submitter checks integrity, redaction and reproducibility. Exclude tokens, passwords, private keys, full environment dumps and real private text. Without approved host/domain/budget/credentials, do not claim public deployment. Invited use also waits for its prerequisites.

## Pause and resume

Checkpoints describe evidence maturity, not a table-before-route recipe. Record actual revisions, last command, established facts, unresolved questions, next evidence and resources you stopped. On resumption compare reality to the record; do not assume previous results still hold. This package starts no services, creates no accounts and changes no database, so its checker has no cluster cleanup obligation.

Unreviewed O06 or unavailable pilot infrastructure stays blocked. This package does not change shared chapter status. Disclose assistance during independent review, explain a real diagnosis, and adapt to a reviewer-selected business change.

## Four claims and known limits

Content completion, author reference validation, student graduation and real public operation stay separate. This package proves only execution of its material tooling, not a student's graduation. Human review needs O06, the required behavior of all 24 scenarios, all gates, the rubric and independent ability. Documentation polish cannot offset unauthorized access, and a script cannot approve graduation.

No student app, migration, authorization, concurrency behavior, release/rollback, database restore or actual pilot was run. There is no public deployment or operation evidence. The tool is not a confidentiality audit, security certification or legal compliance certification. Missing earlier-chapter evidence cannot be upgraded here.

## Sources and packaging

Necessary official sources checked 2026-09-28 are recorded in sources.json: OWASP API1 object authorization, PostgreSQL 18 SQL dump/restoration and RFC 9110 idempotent methods. They clarify acceptance boundaries, not additional implementation requirements.

FILES.json matches the repository sibling g01-graduation-files.json as a per-file allowlist. The ZIP contains requirements, synthetic data, templates, tools and documentation, not submission data, caches, credentials or database storage. Mainline owns registration of canonical loader getGraduationExample, navigation/status and /learning-assets/js2py/g01-graduation.zip. This package edits no shared registry.
