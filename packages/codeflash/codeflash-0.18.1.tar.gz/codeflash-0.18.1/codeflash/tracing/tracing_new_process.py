from __future__ import annotations

import contextlib
import datetime
import importlib
import io
import json
import os
import pickle
import re
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, ClassVar

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from codeflash.cli_cmds.console import console
from codeflash.picklepatch.pickle_patcher import PicklePatcher
from codeflash.tracing.tracing_utils import FunctionModules, filter_files_optimized, module_name_from_file_path

if TYPE_CHECKING:
    from types import FrameType, TracebackType


class FakeCode:
    def __init__(self, filename: str, line: int, name: str) -> None:
        self.co_filename = filename
        self.co_line = line
        self.co_name = name
        self.co_firstlineno = 0

    def __repr__(self) -> str:
        return repr((self.co_filename, self.co_line, self.co_name, None))


class FakeFrame:
    def __init__(self, code: FakeCode, prior: FakeFrame | None) -> None:
        self.f_code = code
        self.f_back = prior
        self.f_locals: dict = {}


def patch_ap_scheduler() -> None:
    if find_spec("apscheduler"):
        import apscheduler.schedulers.background as bg
        import apscheduler.schedulers.blocking as bb
        from apscheduler.schedulers import base

        bg.BackgroundScheduler.start = lambda _, *_a, **_k: None
        bb.BlockingScheduler.start = lambda _, *_a, **_k: None
        base.BaseScheduler.add_job = lambda _, *_a, **_k: None


# Debug this file by simply adding print statements. This file is not meant to be debugged by the debugger.
class Tracer:
    """Use this class as a 'with' context manager to trace a function call.

    Traces function calls, input arguments, and profiling info.
    """

    def __init__(
        self,
        config: dict,
        result_pickle_file_path: Path,
        output: str = "codeflash.trace",
        functions: list[str] | None = None,
        disable: bool = False,  # noqa: FBT001, FBT002
        project_root: Path | None = None,
        max_function_count: int = 256,
        timeout: int | None = None,  # seconds
        command: str = "",
    ) -> None:
        """Use this class to trace function calls.

        :param output: The path to the output trace file
        :param functions: List of functions to trace. If None, trace all functions
        :param disable: Disable the tracer if True
        :param max_function_count: Maximum number of times to trace one function
        :param timeout: Timeout in seconds for the tracer, if the traced code takes more than this time, then tracing
                    stops and normal execution continues. If this is None then no timeout applies
        :param command: The command that initiated the tracing (for metadata storage)
        """
        if functions is None:
            functions = []
        if os.environ.get("CODEFLASH_TRACER_DISABLE", "0") == "1":
            console.rule(
                "Codeflash: Tracer disabled by environment variable CODEFLASH_TRACER_DISABLE", style="bold red"
            )
            disable = True
        self.disable = disable
        self._db_lock: threading.Lock | None = None
        if self.disable:
            return
        if sys.getprofile() is not None or sys.gettrace() is not None:
            console.print(
                "WARNING - Codeflash: Another profiler, debugger or coverage tool is already running. "
                "Please disable it before starting the Codeflash Tracer, both can't run. Codeflash Tracer is DISABLED."
            )
            self.disable = True
            return

        self._db_lock = threading.Lock()

        self.con = None
        self.output_file = Path(output).resolve()
        self.functions = functions
        self.function_modules: list[FunctionModules] = []
        self.function_count = defaultdict(int)
        self.current_file_path = Path(__file__).resolve()
        self.ignored_qualified_functions = {
            f"{self.current_file_path}:Tracer.__exit__",
            f"{self.current_file_path}:Tracer.__enter__",
        }
        self.max_function_count = max_function_count
        self.config = config
        self.project_root = project_root
        console.rule(f"Project Root: {self.project_root}", style="bold blue")
        self.ignored_functions = {"<listcomp>", "<genexpr>", "<dictcomp>", "<setcomp>", "<lambda>", "<module>"}

        self.sanitized_filename = self.sanitize_to_filename(command)
        self.result_pickle_file_path = result_pickle_file_path

        assert timeout is None or timeout > 0, "Timeout should be greater than 0"
        self.timeout = timeout
        self.next_insert = 1000
        self.trace_count = 0
        self.path_cache = {}  # Cache for resolved file paths

        # Profiler variables
        self.bias = 0  # calibration constant
        self.timings = {}
        self.cur = None
        self.start_time = None
        self.timer = time.process_time_ns
        self.total_tt = 0
        self.simulate_call("profiler")
        assert "test_framework" in self.config, "Please specify 'test-framework' in pyproject.toml config file"
        self.t = self.timer()

        # Store command information for metadata table
        self.command = command

    def __enter__(self) -> None:
        if self.disable:
            return
        if getattr(Tracer, "used_once", False):
            console.print(
                "Codeflash: Tracer can only be used once per program run. "
                "Please only enable the Tracer once. Skipping tracing this section."
            )
            self.disable = True
            return
        Tracer.used_once = True

        if Path(self.output_file).exists():
            console.rule("Removing existing trace file", style="bold red")
            console.rule()
        Path(self.output_file).unlink(missing_ok=True)

        self.con = sqlite3.connect(self.output_file, check_same_thread=False)
        cur = self.con.cursor()
        cur.execute("""PRAGMA synchronous = OFF""")
        cur.execute("""PRAGMA journal_mode = WAL""")
        # TODO: Check out if we need to export the function test name as well
        cur.execute(
            "CREATE TABLE function_calls(type TEXT, function TEXT, classname TEXT, filename TEXT, "
            "line_number INTEGER, last_frame_address INTEGER, time_ns INTEGER, args BLOB)"
        )

        # Create metadata table to store command information
        cur.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT)")

        # Store command metadata
        cur.execute("INSERT INTO metadata VALUES (?, ?)", ("command", self.command))
        cur.execute("INSERT INTO metadata VALUES (?, ?)", ("program_name", self.sanitized_filename))
        cur.execute(
            "INSERT INTO metadata VALUES (?, ?)",
            ("functions_filter", json.dumps(self.functions) if self.functions else None),
        )
        cur.execute(
            "INSERT INTO metadata VALUES (?, ?)",
            ("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        )
        cur.execute("INSERT INTO metadata VALUES (?, ?)", ("project_root", str(self.project_root)))
        console.rule("Codeflash: Traced Program Output Begin", style="bold blue")
        frame = sys._getframe(0)  # Get this frame and simulate a call to it  # noqa: SLF001
        self.dispatch["call"](self, frame, 0)
        self.start_time = time.time()
        sys.setprofile(self.trace_callback)
        threading.setprofile(self.trace_callback)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        if self.disable or self._db_lock is None:
            return
        sys.setprofile(None)
        threading.setprofile(None)

        with self._db_lock:
            if self.con is None:
                return

            self.con.commit()  # Commit any pending from tracer_logic
            console.rule("Codeflash: Traced Program Output End", style="bold blue")
            self.create_stats()  # This calls snapshot_stats which uses self.timings

            cur = self.con.cursor()
            cur.execute(
                "CREATE TABLE pstats (filename TEXT, line_number INTEGER, function TEXT, class_name TEXT, "
                "call_count_nonrecursive INTEGER, num_callers INTEGER, total_time_ns INTEGER, "
                "cumulative_time_ns INTEGER, callers BLOB)"
            )
            # self.stats is populated by snapshot_stats() called within create_stats()
            # Ensure self.stats is accessed after create_stats() and within the lock if it involves DB data
            # For now, assuming self.stats is primarily in-memory after create_stats()
            for func, (cc, nc, tt, ct, callers) in self.stats.items():
                remapped_callers = [{"key": k, "value": v} for k, v in callers.items()]
                cur.execute(
                    "INSERT INTO pstats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(Path(func[0]).resolve()),
                        func[1],
                        func[2],
                        func[3],
                        cc,
                        nc,
                        tt,
                        ct,
                        json.dumps(remapped_callers),
                    ),
                )
            self.con.commit()

            self.make_pstats_compatible()  # Modifies self.stats and self.timings in-memory
            self.print_stats("tottime")  # Uses self.stats, prints to console

            cur = self.con.cursor()  # New cursor
            cur.execute("CREATE TABLE total_time (time_ns INTEGER)")
            cur.execute("INSERT INTO total_time VALUES (?)", (self.total_tt,))
            self.con.commit()
            self.con.close()
            self.con = None  # Mark connection as closed

        # filter any functions where we did not capture the return
        self.function_modules = [
            function
            for function in self.function_modules
            if self.function_count[
                str(function.file_name)
                + ":"
                + (function.class_name + "." if function.class_name else "")
                + function.function_name
            ]
            > 0
        ]

        # These modules have been imported here now the tracer is done. It is safe to import codeflash and external modules here

        from contextlib import suppress

        import isort

        from codeflash.tracing.replay_test import create_trace_replay_test
        from codeflash.verification.verification_utils import get_test_file_path

        replay_test = create_trace_replay_test(
            trace_file=self.output_file,
            functions=self.function_modules,
            test_framework=self.config["test_framework"],
            max_run_count=self.max_function_count,
        )
        function_path = "_".join(self.functions) if self.functions else self.sanitized_filename
        test_file_path = get_test_file_path(
            test_dir=Path(self.config["tests_root"]), function_name=function_path, test_type="replay"
        )
        with suppress(Exception):
            replay_test = isort.code(replay_test)

        with Path(test_file_path).open("w", encoding="utf8") as file:
            file.write(replay_test)
        self.replay_test_file_path = test_file_path

        console.print(
            f"Codeflash: Traced {self.trace_count} function calls successfully and replay test created at - {test_file_path}",
            crop=False,
            soft_wrap=False,
            overflow="ignore",
        )
        pickle_data = {"replay_test_file_path": self.replay_test_file_path}
        import pickle

        with self.result_pickle_file_path.open("wb") as file:
            pickle.dump(pickle_data, file)

    def tracer_logic(self, frame: FrameType, event: str) -> None:  # noqa: PLR0911
        if event != "call":
            return
        if None is not self.timeout and (time.time() - self.start_time) > self.timeout:
            sys.setprofile(None)
            threading.setprofile(None)
            console.print(f"Codeflash: Timeout reached! Stopping tracing at {self.timeout} seconds.")
            return
        if self.disable or self._db_lock is None or self.con is None:
            return

        code = frame.f_code

        # Check function name first before resolving path
        if code.co_name in self.ignored_functions:
            return

        # Now resolve file path only if we need it
        co_filename = code.co_filename
        if co_filename in self.path_cache:
            file_name = self.path_cache[co_filename]
        else:
            file_name = Path(co_filename).resolve()
            self.path_cache[co_filename] = file_name
        # TODO : It currently doesn't log the last return call from the first function

        if not file_name.is_relative_to(self.project_root):
            return
        if not file_name.exists():
            return
        if self.functions and code.co_name not in self.functions:
            return
        class_name = None
        arguments = frame.f_locals
        try:
            self_arg = arguments.get("self")
            if self_arg is not None:
                try:
                    class_name = self_arg.__class__.__name__
                except AttributeError:
                    cls_arg = arguments.get("cls")
                    if cls_arg is not None:
                        with contextlib.suppress(AttributeError):
                            class_name = cls_arg.__name__
            else:
                cls_arg = arguments.get("cls")
                if cls_arg is not None:
                    with contextlib.suppress(AttributeError):
                        class_name = cls_arg.__name__
        except:  # noqa: E722
            # someone can override the getattr method and raise an exception. I'm looking at you wrapt
            return

        # Extract class name from co_qualname for static methods that lack self/cls
        if class_name is None and "." in getattr(code, "co_qualname", ""):
            qualname_parts = code.co_qualname.split(".")
            if len(qualname_parts) >= 2:
                class_name = qualname_parts[-2]

        try:
            function_qualified_name = f"{file_name}:{code.co_qualname}"
        except AttributeError:
            function_qualified_name = f"{file_name}:{(class_name + '.' if class_name else '')}{code.co_name}"
        if function_qualified_name in self.ignored_qualified_functions:
            return
        if function_qualified_name not in self.function_count:
            # seeing this function for the first time
            self.function_count[function_qualified_name] = 1
            file_valid = filter_files_optimized(
                file_path=file_name,
                tests_root=Path(self.config["tests_root"]),
                ignore_paths=[Path(p) for p in self.config["ignore_paths"]],
                module_root=Path(self.config["module_root"]),
            )
            if not file_valid:
                # we don't want to trace this function because it cannot be optimized
                self.ignored_qualified_functions.add(function_qualified_name)
                return
            self.function_modules.append(
                FunctionModules(
                    function_name=code.co_name,
                    file_name=file_name,
                    module_name=module_name_from_file_path(file_name, project_root_path=self.project_root),
                    class_name=class_name,
                    line_no=code.co_firstlineno,
                )
            )
        else:
            self.function_count[function_qualified_name] += 1
            if self.function_count[function_qualified_name] >= self.max_function_count:
                self.ignored_qualified_functions.add(function_qualified_name)
                return

        # TODO: Also check if this function arguments are unique from the values logged earlier

        with self._db_lock:
            # Check connection again inside lock, in case __exit__ closed it.
            if self.con is None:
                return

            cur = self.con.cursor()

            t_ns = time.perf_counter_ns()
            original_recursion_limit = sys.getrecursionlimit()
            try:
                # pickling can be a recursive operator, so we need to increase the recursion limit
                sys.setrecursionlimit(10000)
                # We do not pickle self for __init__ to avoid recursion errors, and instead instantiate its class
                # directly with the rest of the arguments in the replay tests. We copy the arguments to avoid memory
                # leaks, bad references or side effects when unpickling.
                arguments_copy = dict(arguments.items())  # Use the local 'arguments' from frame.f_locals
                if class_name and code.co_name == "__init__" and "self" in arguments_copy:
                    del arguments_copy["self"]
                local_vars = PicklePatcher.dumps(arguments_copy, protocol=pickle.HIGHEST_PROTOCOL)
                sys.setrecursionlimit(original_recursion_limit)
            except Exception:
                self.function_count[function_qualified_name] -= 1
                sys.setrecursionlimit(original_recursion_limit)
                return

            cur.execute(
                "INSERT INTO function_calls VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event,
                    code.co_name,
                    class_name,
                    str(file_name),
                    frame.f_lineno,
                    frame.f_back.__hash__(),
                    t_ns,
                    local_vars,
                ),
            )
            self.trace_count += 1
            self.next_insert -= 1
            if self.next_insert == 0:
                self.next_insert = 1000
                self.con.commit()

    def trace_callback(self, frame: FrameType, event: str, arg: str | None) -> None:
        # profiler section
        timer = self.timer
        t = timer() - self.t - self.bias
        if event == "c_call":
            self.c_func_name = arg.__name__

        prof_success = bool(self.dispatch[event](self, frame, t))
        # tracer section
        self.tracer_logic(frame, event)
        # measure the time as the last thing before return
        if prof_success:
            self.t = timer()
        else:
            self.t = timer() - t  # put back unrecorded delta

    def trace_dispatch_call(self, frame: FrameType, t: int) -> int:
        """Handle call events in the profiler."""
        try:
            # In multi-threaded contexts, we need to be more careful about frame comparisons
            if self.cur and frame.f_back is not self.cur[-2]:
                # This happens when we're in a different thread
                rpt, rit, ret, rfn, rframe, rcur = self.cur

                # Only attempt to handle the frame mismatch if we have a valid rframe
                if (
                    not isinstance(rframe, FakeFrame)
                    and hasattr(rframe, "f_back")
                    and hasattr(frame, "f_back")
                    and rframe.f_back is frame.f_back
                ):
                    self.trace_dispatch_return(rframe, 0)

            # Get function information
            fcode = frame.f_code
            arguments = frame.f_locals
            class_name = None
            try:
                if (
                    "self" in arguments
                    and hasattr(arguments["self"], "__class__")
                    and hasattr(arguments["self"].__class__, "__name__")
                ):
                    class_name = arguments["self"].__class__.__name__
                elif "cls" in arguments and hasattr(arguments["cls"], "__name__"):
                    class_name = arguments["cls"].__name__
            except Exception:  # noqa: S110
                pass

            fn = (fcode.co_filename, fcode.co_firstlineno, fcode.co_name, class_name)
            self.cur = (t, 0, 0, fn, frame, self.cur)
            timings = self.timings
            if fn in timings:
                cc, ns, tt, ct, callers = timings[fn]
                timings[fn] = cc, ns + 1, tt, ct, callers
            else:
                timings[fn] = 0, 0, 0, 0, {}
            return 1  # noqa: TRY300
        except Exception:
            # Handle any errors gracefully
            return 0

    def trace_dispatch_exception(self, frame: FrameType, t: int) -> int:
        rpt, rit, ret, rfn, rframe, rcur = self.cur
        if (rframe is not frame) and rcur:
            return self.trace_dispatch_return(rframe, t)
        self.cur = rpt, rit + t, ret, rfn, rframe, rcur
        return 1

    def trace_dispatch_c_call(self, frame: FrameType, t: int) -> int:
        fn = ("", 0, self.c_func_name, None)
        self.cur = (t, 0, 0, fn, frame, self.cur)
        timings = self.timings
        if fn in timings:
            cc, ns, tt, ct, callers = timings[fn]
            timings[fn] = cc, ns + 1, tt, ct, callers
        else:
            timings[fn] = 0, 0, 0, 0, {}
        return 1

    def trace_dispatch_return(self, frame: FrameType, t: int) -> int:
        if not self.cur or not self.cur[-2]:
            return 0

        # In multi-threaded environments, frames can get mismatched
        if frame is not self.cur[-2]:
            # Don't assert in threaded environments - frames can legitimately differ
            if hasattr(frame, "f_back") and hasattr(self.cur[-2], "f_back") and frame is self.cur[-2].f_back:
                self.trace_dispatch_return(self.cur[-2], 0)
            else:
                # We're in a different thread or context, can't continue with this frame
                return 0
        # Prefix "r" means part of the Returning or exiting frame.
        # Prefix "p" means part of the Previous or Parent or older frame.

        rpt, rit, ret, rfn, frame, rcur = self.cur

        # Guard against invalid rcur (w threading)
        if not rcur:
            return 0

        rit = rit + t
        frame_total = rit + ret

        ppt, pit, pet, pfn, pframe, pcur = rcur
        self.cur = ppt, pit + rpt, pet + frame_total, pfn, pframe, pcur

        timings = self.timings
        if rfn not in timings:
            # w threading, rfn can be missing
            timings[rfn] = 0, 0, 0, 0, {}
        cc, ns, tt, ct, callers = timings[rfn]
        if not ns:
            # This is the only occurrence of the function on the stack.
            # Else this is a (directly or indirectly) recursive call, and
            # its cumulative time will get updated when the topmost call to
            # it returns.
            ct = ct + frame_total
            cc = cc + 1

        if pfn in callers:
            # Increment call count between these functions
            callers[pfn] = callers[pfn] + 1
            # Note: This tracks stats such as the amount of time added to ct
            # of this specific call, and the contribution to cc
            # courtesy of this call.
        else:
            callers[pfn] = 1

        timings[rfn] = cc, ns - 1, tt + rit, ct, callers

        return 1

    dispatch: ClassVar[dict[str, Callable[[Tracer, FrameType, int], int]]] = {
        "call": trace_dispatch_call,
        "exception": trace_dispatch_exception,
        "return": trace_dispatch_return,
        "c_call": trace_dispatch_c_call,
        "c_exception": trace_dispatch_return,  # the C function returned
        "c_return": trace_dispatch_return,
    }

    def simulate_call(self, name: str) -> None:
        code = FakeCode("profiler", 0, name)
        pframe = self.cur[-2] if self.cur else None
        frame = FakeFrame(code, pframe)
        self.dispatch["call"](self, frame, 0)

    def simulate_cmd_complete(self) -> None:
        get_time = self.timer
        t = get_time() - self.t
        while self.cur[-1]:
            # We *can* cause assertion errors here if
            # dispatch_trace_return checks for a frame match!
            self.dispatch["return"](self, self.cur[-2], t)
            t = 0
        self.t = get_time() - t

    def print_stats(self, sort: str | int | tuple = -1) -> None:
        if not self.stats:
            console.print("Codeflash: No stats available to print")
            self.total_tt = 0
            return

        if not isinstance(sort, tuple):
            sort = (sort,)

        # First, convert stats to make them pstats-compatible
        try:
            # Initialize empty collections for pstats
            self.files = []
            self.top_level = []

            # Create entirely new dictionaries instead of modifying existing ones
            new_stats = {}
            new_timings = {}

            # Convert stats dictionary
            stats_items = list(self.stats.items())
            for func, stats_data in stats_items:
                try:
                    # Make sure we have 5 elements in stats_data
                    if len(stats_data) != 5:
                        console.print(f"Skipping malformed stats data for {func}: {stats_data}")
                        continue

                    cc, nc, tt, ct, callers = stats_data

                    if len(func) == 4:
                        file_name, line_num, func_name, class_name = func
                        new_func_name = f"{class_name}.{func_name}" if class_name else func_name
                        new_func = (file_name, line_num, new_func_name)
                    else:
                        new_func = func  # Keep as is if already in correct format

                    new_callers = {}
                    callers_items = list(callers.items())
                    for caller_func, count in callers_items:
                        if isinstance(caller_func, tuple):
                            if len(caller_func) == 4:
                                caller_file, caller_line, caller_name, caller_class = caller_func
                                caller_new_name = f"{caller_class}.{caller_name}" if caller_class else caller_name
                                new_caller_func = (caller_file, caller_line, caller_new_name)
                            else:
                                new_caller_func = caller_func
                        else:
                            console.print(f"Unexpected caller format: {caller_func}")
                            new_caller_func = str(caller_func)

                        new_callers[new_caller_func] = count

                    # Store with new format
                    new_stats[new_func] = (cc, nc, tt, ct, new_callers)
                except Exception as e:
                    console.print(f"Error converting stats for {func}: {e}")
                    continue

            timings_items = list(self.timings.items())
            for func, timing_data in timings_items:
                try:
                    if len(timing_data) != 5:
                        console.print(f"Skipping malformed timing data for {func}: {timing_data}")
                        continue

                    cc, ns, tt, ct, callers = timing_data

                    if len(func) == 4:
                        file_name, line_num, func_name, class_name = func
                        new_func_name = f"{class_name}.{func_name}" if class_name else func_name
                        new_func = (file_name, line_num, new_func_name)
                    else:
                        new_func = func

                    new_callers = {}
                    callers_items = list(callers.items())
                    for caller_func, count in callers_items:
                        if isinstance(caller_func, tuple):
                            if len(caller_func) == 4:
                                caller_file, caller_line, caller_name, caller_class = caller_func
                                caller_new_name = f"{caller_class}.{caller_name}" if caller_class else caller_name
                                new_caller_func = (caller_file, caller_line, caller_new_name)
                            else:
                                new_caller_func = caller_func
                        else:
                            console.print(f"Unexpected caller format: {caller_func}")
                            new_caller_func = str(caller_func)

                        new_callers[new_caller_func] = count

                    new_timings[new_func] = (cc, ns, tt, ct, new_callers)
                except Exception as e:
                    console.print(f"Error converting timings for {func}: {e}")
                    continue

            self.stats = new_stats
            self.timings = new_timings

            self.total_tt = sum(tt for _, _, tt, _, _ in self.stats.values())

            total_calls = sum(cc for cc, _, _, _, _ in self.stats.values())
            total_primitive = sum(nc for _, nc, _, _, _ in self.stats.values())

            summary = Text.assemble(
                f"{total_calls:,} function calls ",
                ("(" + f"{total_primitive:,} primitive calls" + ")", "dim"),
                f" in {self.total_tt / 1e6:.3f}milliseconds",
            )

            console.print(Align.center(Panel(summary, border_style="blue", width=80, padding=(0, 2), expand=False)))

            table = Table(
                show_header=True,
                header_style="bold magenta",
                border_style="blue",
                title="[bold]Function Profile[/bold] (ordered by internal time)",
                title_style="cyan",
                caption=f"Showing top {min(25, len(self.stats))} of {len(self.stats)} functions",
            )

            table.add_column("Calls", justify="right", style="green", width=10)
            table.add_column("Time (ms)", justify="right", style="cyan", width=10)
            table.add_column("Per Call", justify="right", style="cyan", width=10)
            table.add_column("Cum (ms)", justify="right", style="yellow", width=10)
            table.add_column("Cum/Call", justify="right", style="yellow", width=10)
            table.add_column("Function", style="blue")

            sorted_stats = sorted(
                ((func, stats) for func, stats in self.stats.items() if isinstance(func, tuple) and len(func) == 3),
                key=lambda x: x[1][2],  # Sort by tt (internal time)
                reverse=True,
            )[:25]  # Limit to top 25

            # Format and add each row to the table
            for func, (cc, nc, tt, ct, _) in sorted_stats:
                filename, lineno, funcname = func

                # Format calls - show recursive format if different
                calls_str = f"{cc}/{nc}" if cc != nc else f"{cc:,}"

                # Convert to milliseconds
                tt_ms = tt / 1e6
                ct_ms = ct / 1e6

                # Calculate per-call times
                per_call = tt_ms / cc if cc > 0 else 0
                cum_per_call = ct_ms / nc if nc > 0 else 0
                base_filename = Path(filename).name
                file_link = f"[link=file://{filename}]{base_filename}[/link]"

                table.add_row(
                    calls_str,
                    f"{tt_ms:.3f}",
                    f"{per_call:.3f}",
                    f"{ct_ms:.3f}",
                    f"{cum_per_call:.3f}",
                    f"{funcname} [dim]({file_link}:{lineno})[/dim]",
                )

            console.print(Align.center(table))

        except Exception as e:
            console.print(f"[bold red]Error in stats processing:[/bold red] {e}")
            console.print(f"Traced {self.trace_count:,} function calls")
            self.total_tt = 0

    def make_pstats_compatible(self) -> None:
        # delete the extra class_name item from the function tuple
        self.files = []
        self.top_level = []
        new_stats = {}
        for func, (cc, ns, tt, ct, callers) in self.stats.items():
            new_callers = {(k[0], k[1], k[2]): v for k, v in callers.items()}
            new_stats[(func[0], func[1], func[2])] = (cc, ns, tt, ct, new_callers)
        new_timings = {}
        for func, (cc, ns, tt, ct, callers) in self.timings.items():
            new_callers = {(k[0], k[1], k[2]): v for k, v in callers.items()}
            new_timings[(func[0], func[1], func[2])] = (cc, ns, tt, ct, new_callers)
        self.stats = new_stats
        self.timings = new_timings

    def dump_stats(self, file: str) -> None:
        import marshal

        with Path(file).open("wb") as f:
            marshal.dump(self.stats, f)

    def create_stats(self) -> None:
        self.simulate_cmd_complete()
        self.snapshot_stats()

    def snapshot_stats(self) -> None:
        self.stats = {}
        for func, (cc, _ns, tt, ct, caller_dict) in list(self.timings.items()):
            callers = caller_dict.copy()
            nc = 0
            for callcnt in callers.values():
                nc += callcnt
            self.stats[func] = cc, nc, tt, ct, callers

    def sanitize_to_filename(self, arg: str) -> str:
        # Replace newlines with underscores
        arg = arg.replace("\n", "_").replace("\r", "_")

        # Replace contiguous whitespace (including tabs and multiple spaces) with a single underscore
        # Limit to 5 whitespace splits
        parts = re.split(r"\s+", arg)
        if len(parts) > 5:
            parts = parts[:5]

        arg = "_".join(parts)

        # Remove all characters that are not alphanumeric, underscore, or dot
        arg = re.sub(r"[^\w._]", "", arg)

        # Avoid filenames starting or ending with a dot or underscore
        arg = arg.strip("._")

        # Limit to 100 characters
        arg = arg[:100]

        # Fallback if resulting name is empty
        return arg or "untitled"

    def runctx(self, cmd: str, global_vars: dict[str, Any], local_vars: dict[str, Any]) -> Tracer | None:
        self.__enter__()
        try:
            exec(cmd, global_vars, local_vars)  # noqa: S102
        finally:
            self.__exit__(None, None, None)
        return self


if __name__ == "__main__":
    args_dict = json.loads(sys.argv[-1])
    sys.argv = sys.argv[1:-1]
    patch_ap_scheduler()
    if args_dict["module"]:
        import runpy

        code = "run_module(modname, run_name='__main__')"
        globs = {"run_module": runpy.run_module, "modname": args_dict["progname"]}
    else:
        sys.path.insert(0, str(Path(args_dict["progname"]).resolve().parent))
        with io.open_code(args_dict["progname"]) as fp:
            code = compile(fp.read(), args_dict["progname"], "exec")
        spec = importlib.machinery.ModuleSpec(name="__main__", loader=None, origin=args_dict["progname"])
        globs = {
            "__spec__": spec,
            "__file__": spec.origin,
            "__name__": spec.name,
            "__package__": None,
            "__cached__": None,
        }
    args_dict["config"]["module_root"] = Path(args_dict["config"]["module_root"])
    args_dict["config"]["tests_root"] = Path(args_dict["config"]["tests_root"])
    tracer = Tracer(
        config=args_dict["config"],
        output=Path(args_dict["output"]),
        functions=args_dict["functions"],
        max_function_count=args_dict["max_function_count"],
        timeout=args_dict["timeout"],
        command=args_dict["command"],
        disable=args_dict["disable"],
        result_pickle_file_path=Path(args_dict["result_pickle_file_path"]),
        project_root=Path(args_dict["project_root"]),
    )
    tracer.runctx(code, globs, None)
