import asyncio
import subprocess
import sys
from pathlib import Path

import pytest
from capacity import Meter, bounded, limited_job
from ownership import cancelled, hold_file, timed_out
from scheduling import blocking, creation, drain, offloaded, scheduled, sequential

ROOT = Path(__file__).resolve().parents[1]


def test_coroutine_call_does_not_run_body():
    assert asyncio.run(creation()) == ["called:no-body-yet", "A:start", "A:end"]


def test_direct_await_is_sequential():
    assert asyncio.run(sequential()) == ["A:start", "A:end", "B:start", "B:end"]


def test_tasks_both_enter_before_completion():
    events = asyncio.run(scheduled())
    pivot = events.index("owner:both-entered")
    assert set(events[:pivot]) == {"A:start", "B:start"}
    assert events[pivot + 1:] == ["B:end", "A:end"]


def test_sync_block_delays_ready_callback():
    assert asyncio.run(blocking()) == [
        "sync:start", "sync:end", "callback:ran", "owner:resumed"
    ]


def test_thread_work_is_explicitly_joined():
    assert asyncio.run(offloaded()) == [
        "loop:responsive-while-thread-waits", "thread:returned"
    ]


def test_cancellation_is_not_success():
    assert asyncio.run(cancelled()) == ["file:opened", "file:closed", "owner:cancelled"]


def test_deadline_runs_finally_before_timeout_reaches_owner():
    assert asyncio.run(timed_out()) == ["file:opened", "file:closed", "owner:timeout"]


@pytest.mark.parametrize("exit_mode", ["normal", "cancel"])
def test_real_file_is_closed_and_rejects_writes(exit_mode):
    async def scenario():
        events, handles = [], []
        entered, release = asyncio.Event(), asyncio.Event()
        task = asyncio.create_task(hold_file(events, entered, release, handles))
        try:
            await entered.wait()
            assert not handles[0].closed
            if exit_mode == "cancel":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                release.set()
                await task
            assert handles[0].closed
            with pytest.raises(ValueError, match="closed"):
                handles[0].write("not allowed")
        finally:
            await drain([task])
    asyncio.run(scenario())


def test_cancel_before_start_acquires_nothing():
    async def scenario():
        events, handles = [], []
        task = asyncio.create_task(hold_file(events, asyncio.Event(), asyncio.Event(), handles))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert events == handles == []
    asyncio.run(scenario())


@pytest.mark.parametrize("limit", [1, 2, 3, 4])
def test_capacity(limit):
    assert asyncio.run(bounded(limit)) == f"peak={limit} active=0"


def test_waiter_cancellation_does_not_leak_or_invent_permit():
    async def scenario():
        slots, meter = asyncio.Semaphore(1), Meter()
        entered = [asyncio.Event(), asyncio.Event()]
        release = [asyncio.Event(), asyncio.Event()]
        first = asyncio.create_task(limited_job(0, slots, meter, entered, release))
        second = asyncio.create_task(limited_job(1, slots, meter, entered, release))
        try:
            await entered[0].wait()
            await asyncio.sleep(0)  # Let second reach the occupied semaphore.
            assert not entered[1].is_set()
            second.cancel()
            with pytest.raises(asyncio.CancelledError):
                await second
            assert slots.locked() and meter.active == 1
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert meter.active == 0
            async with asyncio.timeout(1):
                await slots.acquire()  # Public behavior, not _value inspection.
            assert slots.locked()
            slots.release()
        finally:
            await drain([first, second])
    asyncio.run(scenario())


def test_await_already_ready_event_need_not_yield():
    async def scenario():
        events = []
        gate = asyncio.Event()
        gate.set()
        asyncio.get_running_loop().call_soon(events.append, "callback")
        await gate.wait()
        assert events == []
        await asyncio.sleep(0)
        assert events == ["callback"]
    asyncio.run(scenario())


@pytest.mark.parametrize("script,code,needle", [
    ("reuse.py", 1, "cannot reuse already awaited coroutine"),
    ("swallow.py", 0, "result=pretend-success cancelled=False"),
    ("forgotten.py", 0, "events=[]; RuntimeWarning: coroutine was never awaited"),
])
def test_actual_failures(script, code, needle):
    run = subprocess.run([sys.executable, str(ROOT / "errors" / script)],
                         capture_output=True, text=True, timeout=10)
    assert run.returncode == code
    assert needle in run.stdout + run.stderr
