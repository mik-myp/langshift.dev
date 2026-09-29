import json
from psycopg import IsolationLevel
import labctl
import concurrency

scenarios = [
    ("failed_second_step", concurrency.failed_second_step),
    ("read_committed", lambda: concurrency.snapshot(IsolationLevel.READ_COMMITTED)),
    ("repeatable_read", lambda: concurrency.snapshot(IsolationLevel.REPEATABLE_READ)),
    ("lost_update", concurrency.lost_update),
    ("atomic_increment", lambda: concurrency.overlapping_write("increment")),
    ("unique_race", lambda: concurrency.overlapping_write("unique")),
    ("lock_timeout", concurrency.lock_timeout),
    ("serialization_conflict", concurrency.serialization_conflict),
]
for name, scenario in scenarios:
    labctl.reset()
    print(name, json.dumps(scenario(), sort_keys=True))
