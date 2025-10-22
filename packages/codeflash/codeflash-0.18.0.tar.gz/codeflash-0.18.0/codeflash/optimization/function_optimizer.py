from __future__ import annotations

import ast
import concurrent.futures
import os
import queue
import random
import subprocess
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import libcst as cst
from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

from codeflash.api.aiservice import AiServiceClient, AIServiceRefinerRequest, LocalAiServiceClient
from codeflash.api.cfapi import CFWEBAPP_BASE_URL, add_code_context_hash, create_staging, mark_optimization_success
from codeflash.benchmarking.utils import process_benchmark_data
from codeflash.cli_cmds.console import code_print, console, logger, lsp_log, progress_bar
from codeflash.code_utils import env_utils
from codeflash.code_utils.code_extractor import get_opt_review_metrics
from codeflash.code_utils.code_replacer import (
    add_custom_marker_to_all_tests,
    modify_autouse_fixture,
    replace_function_definitions_in_module,
)
from codeflash.code_utils.code_utils import (
    ImportErrorPattern,
    cleanup_paths,
    create_rank_dictionary_compact,
    diff_length,
    file_name_from_test_module_name,
    get_run_tmp_file,
    module_name_from_file_path,
    restore_conftest,
    unified_diff_strings,
)
from codeflash.code_utils.config_consts import (
    COVERAGE_THRESHOLD,
    INDIVIDUAL_TESTCASE_TIMEOUT,
    N_CANDIDATES_EFFECTIVE,
    N_CANDIDATES_LP_EFFECTIVE,
    N_TESTS_TO_GENERATE_EFFECTIVE,
    REPEAT_OPTIMIZATION_PROBABILITY,
    TOTAL_LOOPING_TIME_EFFECTIVE,
)
from codeflash.code_utils.deduplicate_code import normalize_code
from codeflash.code_utils.edit_generated_tests import (
    add_runtime_comments_to_generated_tests,
    remove_functions_from_generated_tests,
)
from codeflash.code_utils.env_utils import get_pr_number
from codeflash.code_utils.formatter import format_code, sort_imports
from codeflash.code_utils.git_utils import git_root_dir
from codeflash.code_utils.instrument_existing_tests import inject_profiling_into_existing_test
from codeflash.code_utils.line_profile_utils import add_decorator_imports
from codeflash.code_utils.static_analysis import get_first_top_level_function_or_method_ast
from codeflash.code_utils.time_utils import humanize_runtime
from codeflash.context import code_context_extractor
from codeflash.context.unused_definition_remover import detect_unused_helper_functions, revert_unused_helper_functions
from codeflash.discovery.functions_to_optimize import was_function_previously_optimized
from codeflash.either import Failure, Success, is_successful
from codeflash.lsp.helpers import is_LSP_enabled, report_to_markdown_table, tree_to_markdown
from codeflash.lsp.lsp_message import LspCodeMessage, LspMarkdownMessage
from codeflash.models.ExperimentMetadata import ExperimentMetadata
from codeflash.models.models import (
    BestOptimization,
    CodeOptimizationContext,
    GeneratedTests,
    GeneratedTestsList,
    OptimizationSet,
    OptimizedCandidate,
    OptimizedCandidateResult,
    OriginalCodeBaseline,
    TestFile,
    TestFiles,
    TestingMode,
    TestResults,
    TestType,
)
from codeflash.result.create_pr import check_create_pr, existing_tests_source_for
from codeflash.result.critic import (
    coverage_critic,
    performance_gain,
    quantity_of_tests_critic,
    speedup_critic,
    throughput_gain,
)
from codeflash.result.explanation import Explanation
from codeflash.telemetry.posthog_cf import ph
from codeflash.verification.concolic_testing import generate_concolic_tests
from codeflash.verification.equivalence import compare_test_results
from codeflash.verification.instrument_codeflash_capture import instrument_codeflash_capture
from codeflash.verification.parse_line_profile_test_output import parse_line_profile_results
from codeflash.verification.parse_test_output import calculate_function_throughput_from_test_results, parse_test_results
from codeflash.verification.test_runner import run_behavioral_tests, run_benchmarking_tests, run_line_profile_tests
from codeflash.verification.verification_utils import get_test_file_path
from codeflash.verification.verifier import generate_tests

if TYPE_CHECKING:
    from argparse import Namespace

    from codeflash.discovery.functions_to_optimize import FunctionToOptimize
    from codeflash.either import Result
    from codeflash.models.models import (
        BenchmarkKey,
        CodeStringsMarkdown,
        CoverageData,
        FunctionCalledInTest,
        FunctionSource,
    )
    from codeflash.verification.verification_utils import TestConfig


class CandidateProcessor:
    """Handles candidate processing using a queue-based approach."""

    def __init__(
        self,
        initial_candidates: list,
        future_line_profile_results: concurrent.futures.Future,
        future_all_refinements: list,
    ) -> None:
        self.candidate_queue = queue.Queue()
        self.line_profiler_done = False
        self.refinement_done = False
        self.candidate_len = len(initial_candidates)

        # Initialize queue with initial candidates
        for candidate in initial_candidates:
            self.candidate_queue.put(candidate)

        self.future_line_profile_results = future_line_profile_results
        self.future_all_refinements = future_all_refinements

    def get_next_candidate(self) -> OptimizedCandidate | None:
        """Get the next candidate from the queue, handling async results as needed."""
        try:
            return self.candidate_queue.get_nowait()
        except queue.Empty:
            return self._handle_empty_queue()

    def _handle_empty_queue(self) -> OptimizedCandidate | None:
        """Handle empty queue by checking for pending async results."""
        if not self.line_profiler_done:
            return self._process_line_profiler_results()
        if self.line_profiler_done and not self.refinement_done:
            return self._process_refinement_results()
        return None  # All done

    def _process_line_profiler_results(self) -> OptimizedCandidate | None:
        """Process line profiler results and add to queue."""
        logger.debug("all candidates processed, await candidates from line profiler")
        concurrent.futures.wait([self.future_line_profile_results])
        line_profile_results = self.future_line_profile_results.result()

        for candidate in line_profile_results:
            self.candidate_queue.put(candidate)

        self.candidate_len += len(line_profile_results)
        logger.info(f"Added results from line profiler to candidates, total candidates now: {self.candidate_len}")
        self.line_profiler_done = True

        return self.get_next_candidate()

    def _process_refinement_results(self) -> OptimizedCandidate | None:
        """Process refinement results and add to queue."""
        if self.future_all_refinements:
            logger.info("loading|Refining generated code for improved quality and performance...")
        concurrent.futures.wait(self.future_all_refinements)
        refinement_response = []

        for future_refinement in self.future_all_refinements:
            possible_refinement = future_refinement.result()
            if len(possible_refinement) > 0:
                refinement_response.append(possible_refinement[0])

        for candidate in refinement_response:
            self.candidate_queue.put(candidate)

        self.candidate_len += len(refinement_response)
        if len(refinement_response) > 0:
            logger.info(
                f"Added {len(refinement_response)} candidates from refinement, total candidates now: {self.candidate_len}"
            )
        self.refinement_done = True

        return self.get_next_candidate()

    def is_done(self) -> bool:
        """Check if processing is complete."""
        return self.line_profiler_done and self.refinement_done and self.candidate_queue.empty()


class FunctionOptimizer:
    def __init__(
        self,
        function_to_optimize: FunctionToOptimize,
        test_cfg: TestConfig,
        function_to_optimize_source_code: str = "",
        function_to_tests: dict[str, set[FunctionCalledInTest]] | None = None,
        function_to_optimize_ast: ast.FunctionDef | ast.AsyncFunctionDef | None = None,
        aiservice_client: AiServiceClient | None = None,
        function_benchmark_timings: dict[BenchmarkKey, int] | None = None,
        total_benchmark_timings: dict[BenchmarkKey, int] | None = None,
        args: Namespace | None = None,
        replay_tests_dir: Path | None = None,
    ) -> None:
        self.project_root = test_cfg.project_root_path
        self.test_cfg = test_cfg
        self.aiservice_client = aiservice_client if aiservice_client else AiServiceClient()
        self.function_to_optimize = function_to_optimize
        self.function_to_optimize_source_code = (
            function_to_optimize_source_code
            if function_to_optimize_source_code
            else function_to_optimize.file_path.read_text(encoding="utf8")
        )
        if not function_to_optimize_ast:
            original_module_ast = ast.parse(function_to_optimize_source_code)
            self.function_to_optimize_ast = get_first_top_level_function_or_method_ast(
                function_to_optimize.function_name, function_to_optimize.parents, original_module_ast
            )
        else:
            self.function_to_optimize_ast = function_to_optimize_ast
        self.function_to_tests = function_to_tests if function_to_tests else {}

        self.experiment_id = os.getenv("CODEFLASH_EXPERIMENT_ID", None)
        self.local_aiservice_client = LocalAiServiceClient() if self.experiment_id else None
        self.test_files = TestFiles(test_files=[])
        self.args = args  # Check defaults for these
        self.function_trace_id: str = str(uuid.uuid4())
        self.original_module_path = module_name_from_file_path(self.function_to_optimize.file_path, self.project_root)

        self.function_benchmark_timings = function_benchmark_timings if function_benchmark_timings else {}
        self.total_benchmark_timings = total_benchmark_timings if total_benchmark_timings else {}
        self.replay_tests_dir = replay_tests_dir if replay_tests_dir else None
        self.generate_and_instrument_tests_results: (
            tuple[GeneratedTestsList, dict[str, set[FunctionCalledInTest]], OptimizationSet] | None
        ) = None
        n_tests = N_TESTS_TO_GENERATE_EFFECTIVE
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=n_tests + 2 if self.experiment_id is None else n_tests + 3
        )

    def can_be_optimized(self) -> Result[tuple[bool, CodeOptimizationContext, dict[Path, str]], str]:
        should_run_experiment = self.experiment_id is not None
        logger.debug(f"Function Trace ID: {self.function_trace_id}")
        ph("cli-optimize-function-start", {"function_trace_id": self.function_trace_id})
        self.cleanup_leftover_test_return_values()
        file_name_from_test_module_name.cache_clear()
        ctx_result = self.get_code_optimization_context()
        if not is_successful(ctx_result):
            return Failure(ctx_result.failure())
        code_context: CodeOptimizationContext = ctx_result.unwrap()
        original_helper_code: dict[Path, str] = {}
        helper_function_paths = {hf.file_path for hf in code_context.helper_functions}
        for helper_function_path in helper_function_paths:
            with helper_function_path.open(encoding="utf8") as f:
                helper_code = f.read()
                original_helper_code[helper_function_path] = helper_code

        # Random here means that we still attempt optimization with a fractional chance to see if
        # last time we could not find an optimization, maybe this time we do.
        # Random is before as a performance optimization, swapping the two 'and' statements has the same effect
        if random.random() > REPEAT_OPTIMIZATION_PROBABILITY and was_function_previously_optimized(  # noqa: S311
            self.function_to_optimize, code_context, self.args
        ):
            return Failure("Function optimization previously attempted, skipping.")

        return Success((should_run_experiment, code_context, original_helper_code))

    def generate_and_instrument_tests(
        self, code_context: CodeOptimizationContext, *, should_run_experiment: bool
    ) -> Result[
        tuple[
            GeneratedTestsList,
            dict[str, set[FunctionCalledInTest]],
            str,
            OptimizationSet,
            list[Path],
            list[Path],
            set[Path],
            dict | None,
        ]
    ]:
        """Generate and instrument tests, returning all necessary data for optimization."""
        n_tests = N_TESTS_TO_GENERATE_EFFECTIVE
        generated_test_paths = [
            get_test_file_path(
                self.test_cfg.tests_root, self.function_to_optimize.function_name, test_index, test_type="unit"
            )
            for test_index in range(n_tests)
        ]
        generated_perf_test_paths = [
            get_test_file_path(
                self.test_cfg.tests_root, self.function_to_optimize.function_name, test_index, test_type="perf"
            )
            for test_index in range(n_tests)
        ]

        with progress_bar(
            f"Generating new tests and optimizations for function '{self.function_to_optimize.function_name}'",
            transient=True,
            revert_to_print=bool(get_pr_number()),
        ):
            generated_results = self.generate_tests_and_optimizations(
                testgen_context=code_context.testgen_context,
                read_writable_code=code_context.read_writable_code,
                read_only_context_code=code_context.read_only_context_code,
                helper_functions=code_context.helper_functions,
                generated_test_paths=generated_test_paths,
                generated_perf_test_paths=generated_perf_test_paths,
                run_experiment=should_run_experiment,
            )

        if not is_successful(generated_results):
            return Failure(generated_results.failure())

        generated_tests: GeneratedTestsList
        optimizations_set: OptimizationSet
        count_tests, generated_tests, function_to_concolic_tests, concolic_test_str, optimizations_set = (
            generated_results.unwrap()
        )

        for i, generated_test in enumerate(generated_tests.generated_tests):
            with generated_test.behavior_file_path.open("w", encoding="utf8") as f:
                f.write(generated_test.instrumented_behavior_test_source)
            with generated_test.perf_file_path.open("w", encoding="utf8") as f:
                f.write(generated_test.instrumented_perf_test_source)
            self.test_files.add(
                TestFile(
                    instrumented_behavior_file_path=generated_test.behavior_file_path,
                    benchmarking_file_path=generated_test.perf_file_path,
                    original_file_path=None,
                    original_source=generated_test.generated_original_test_source,
                    test_type=TestType.GENERATED_REGRESSION,
                    tests_in_file=None,  # This is currently unused. We can discover the tests in the file if needed.
                )
            )
            logger.info(f"Generated test {i + 1}/{count_tests}:")
            code_print(generated_test.generated_original_test_source, file_name=f"test_{i + 1}.py")
        if concolic_test_str:
            logger.info(f"Generated test {count_tests}/{count_tests}:")
            code_print(concolic_test_str)

        function_to_all_tests = {
            key: self.function_to_tests.get(key, set()) | function_to_concolic_tests.get(key, set())
            for key in set(self.function_to_tests) | set(function_to_concolic_tests)
        }
        instrumented_unittests_created_for_function = self.instrument_existing_tests(function_to_all_tests)

        original_conftest_content = None
        if self.args.override_fixtures:
            logger.info("Disabling all autouse fixtures associated with the generated test files")
            original_conftest_content = modify_autouse_fixture(generated_test_paths + generated_perf_test_paths)
            logger.info("Add custom marker to generated test files")
            add_custom_marker_to_all_tests(generated_test_paths + generated_perf_test_paths)

        return Success(
            (
                generated_tests,
                function_to_concolic_tests,
                concolic_test_str,
                optimizations_set,
                generated_test_paths,
                generated_perf_test_paths,
                instrumented_unittests_created_for_function,
                original_conftest_content,
            )
        )

    # note: this isn't called by the lsp, only called by cli
    def optimize_function(self) -> Result[BestOptimization, str]:
        initialization_result = self.can_be_optimized()
        if not is_successful(initialization_result):
            return Failure(initialization_result.failure())

        should_run_experiment, code_context, original_helper_code = initialization_result.unwrap()

        code_print(
            code_context.read_writable_code.flat,
            file_name=self.function_to_optimize.file_path,
            function_name=self.function_to_optimize.function_name,
        )

        test_setup_result = self.generate_and_instrument_tests(  # also generates optimizations
            code_context, should_run_experiment=should_run_experiment
        )
        if not is_successful(test_setup_result):
            return Failure(test_setup_result.failure())

        (
            generated_tests,
            function_to_concolic_tests,
            concolic_test_str,
            optimizations_set,
            generated_test_paths,
            generated_perf_test_paths,
            instrumented_unittests_created_for_function,
            original_conftest_content,
        ) = test_setup_result.unwrap()

        baseline_setup_result = self.setup_and_establish_baseline(
            code_context=code_context,
            original_helper_code=original_helper_code,
            function_to_concolic_tests=function_to_concolic_tests,
            generated_test_paths=generated_test_paths,
            generated_perf_test_paths=generated_perf_test_paths,
            instrumented_unittests_created_for_function=instrumented_unittests_created_for_function,
            original_conftest_content=original_conftest_content,
        )

        if not is_successful(baseline_setup_result):
            return Failure(baseline_setup_result.failure())

        (
            function_to_optimize_qualified_name,
            function_to_all_tests,
            original_code_baseline,
            test_functions_to_remove,
            file_path_to_helper_classes,
        ) = baseline_setup_result.unwrap()

        best_optimization = self.find_and_process_best_optimization(
            optimizations_set=optimizations_set,
            code_context=code_context,
            original_code_baseline=original_code_baseline,
            original_helper_code=original_helper_code,
            file_path_to_helper_classes=file_path_to_helper_classes,
            function_to_optimize_qualified_name=function_to_optimize_qualified_name,
            function_to_all_tests=function_to_all_tests,
            generated_tests=generated_tests,
            test_functions_to_remove=test_functions_to_remove,
            concolic_test_str=concolic_test_str,
        )

        # Add function to code context hash if in gh actions

        add_code_context_hash(code_context.hashing_code_context_hash)

        if self.args.override_fixtures:
            restore_conftest(original_conftest_content)
        if not best_optimization:
            return Failure(f"No best optimizations found for function {self.function_to_optimize.qualified_name}")
        return Success(best_optimization)

    def determine_best_candidate(
        self,
        *,
        candidates: list[OptimizedCandidate],
        code_context: CodeOptimizationContext,
        original_code_baseline: OriginalCodeBaseline,
        original_helper_code: dict[Path, str],
        file_path_to_helper_classes: dict[Path, set[str]],
        exp_type: str,
    ) -> BestOptimization | None:
        best_optimization: BestOptimization | None = None
        _best_runtime_until_now = original_code_baseline.runtime

        speedup_ratios: dict[str, float | None] = {}
        optimized_runtimes: dict[str, float | None] = {}
        is_correct = {}
        optimized_line_profiler_results: dict[str, str] = {}

        logger.info(
            f"Determining best optimization candidate (out of {len(candidates)}) for "
            f"{self.function_to_optimize.qualified_name}…"
        )
        console.rule()

        future_all_refinements: list[concurrent.futures.Future] = []
        ast_code_to_id = {}
        valid_optimizations = []
        optimizations_post = {}  # we need to overwrite some opt candidates' code strings as they are no longer evaluated, instead their shorter/longer versions might be evaluated

        # Start a new thread for AI service request
        ai_service_client = self.aiservice_client if exp_type == "EXP0" else self.local_aiservice_client
        future_line_profile_results = self.executor.submit(
            ai_service_client.optimize_python_code_line_profiler,
            source_code=code_context.read_writable_code.markdown,
            dependency_code=code_context.read_only_context_code,
            trace_id=self.function_trace_id[:-4] + exp_type if self.experiment_id else self.function_trace_id,
            line_profiler_results=original_code_baseline.line_profile_results["str_out"],
            num_candidates=N_CANDIDATES_LP_EFFECTIVE,
            experiment_metadata=ExperimentMetadata(
                id=self.experiment_id, group="control" if exp_type == "EXP0" else "experiment"
            )
            if self.experiment_id
            else None,
        )

        # Initialize candidate processor
        processor = CandidateProcessor(candidates, future_line_profile_results, future_all_refinements)
        candidate_index = 0

        # Process candidates using queue-based approach
        while not processor.is_done():
            candidate = processor.get_next_candidate()
            if candidate is None:
                logger.debug("everything done, exiting")
                break

            try:
                candidate_index += 1
                get_run_tmp_file(Path(f"test_return_values_{candidate_index}.bin")).unlink(missing_ok=True)
                get_run_tmp_file(Path(f"test_return_values_{candidate_index}.sqlite")).unlink(missing_ok=True)
                logger.info(f"h3|Optimization candidate {candidate_index}/{processor.candidate_len}:")
                code_print(candidate.source_code.flat, file_name=f"candidate_{candidate_index}.py")
                # map ast normalized code to diff len, unnormalized code
                # map opt id to the shortest unnormalized code
                try:
                    did_update = self.replace_function_and_helpers_with_optimized_code(
                        code_context=code_context,
                        optimized_code=candidate.source_code,
                        original_helper_code=original_helper_code,
                    )
                    if not did_update:
                        logger.warning(
                            "force_lsp|No functions were replaced in the optimized code. Skipping optimization candidate."
                        )
                        console.rule()
                        continue
                except (ValueError, SyntaxError, cst.ParserSyntaxError, AttributeError) as e:
                    logger.error(e)
                    self.write_code_and_helpers(
                        self.function_to_optimize_source_code, original_helper_code, self.function_to_optimize.file_path
                    )
                    continue
                # check if this code has been evaluated before by checking the ast normalized code string
                normalized_code = normalize_code(candidate.source_code.flat.strip())
                if normalized_code in ast_code_to_id:
                    logger.info(
                        "Current candidate has been encountered before in testing, Skipping optimization candidate."
                    )
                    past_opt_id = ast_code_to_id[normalized_code]["optimization_id"]
                    # update speedup ratio, is_correct, optimizations_post, optimized_line_profiler_results, optimized_runtimes
                    speedup_ratios[candidate.optimization_id] = speedup_ratios[past_opt_id]
                    is_correct[candidate.optimization_id] = is_correct[past_opt_id]
                    optimized_runtimes[candidate.optimization_id] = optimized_runtimes[past_opt_id]
                    # line profiler results only available for successful runs
                    if past_opt_id in optimized_line_profiler_results:
                        optimized_line_profiler_results[candidate.optimization_id] = optimized_line_profiler_results[
                            past_opt_id
                        ]
                    optimizations_post[candidate.optimization_id] = ast_code_to_id[normalized_code][
                        "shorter_source_code"
                    ].markdown
                    optimizations_post[past_opt_id] = ast_code_to_id[normalized_code]["shorter_source_code"].markdown
                    new_diff_len = diff_length(candidate.source_code.flat, code_context.read_writable_code.flat)
                    if (
                        new_diff_len < ast_code_to_id[normalized_code]["diff_len"]
                    ):  # new candidate has a shorter diff than the previously encountered one
                        ast_code_to_id[normalized_code]["shorter_source_code"] = candidate.source_code
                        ast_code_to_id[normalized_code]["diff_len"] = new_diff_len
                    continue
                ast_code_to_id[normalized_code] = {
                    "optimization_id": candidate.optimization_id,
                    "shorter_source_code": candidate.source_code,
                    "diff_len": diff_length(candidate.source_code.flat, code_context.read_writable_code.flat),
                }
                run_results = self.run_optimized_candidate(
                    optimization_candidate_index=candidate_index,
                    baseline_results=original_code_baseline,
                    original_helper_code=original_helper_code,
                    file_path_to_helper_classes=file_path_to_helper_classes,
                )
                console.rule()
                if not is_successful(run_results):
                    optimized_runtimes[candidate.optimization_id] = None
                    is_correct[candidate.optimization_id] = False
                    speedup_ratios[candidate.optimization_id] = None
                else:
                    candidate_result: OptimizedCandidateResult = run_results.unwrap()
                    best_test_runtime = candidate_result.best_test_runtime
                    optimized_runtimes[candidate.optimization_id] = best_test_runtime
                    is_correct[candidate.optimization_id] = True
                    perf_gain = performance_gain(
                        original_runtime_ns=original_code_baseline.runtime, optimized_runtime_ns=best_test_runtime
                    )
                    speedup_ratios[candidate.optimization_id] = perf_gain

                    tree = Tree(f"Candidate #{candidate_index} - Runtime Information ⌛")
                    benchmark_tree = None
                    if speedup_critic(
                        candidate_result,
                        original_code_baseline.runtime,
                        best_runtime_until_now=None,
                        original_async_throughput=original_code_baseline.async_throughput,
                        best_throughput_until_now=None,
                    ) and quantity_of_tests_critic(candidate_result):
                        tree.add("This candidate is faster than the original code. 🚀")  # TODO: Change this description
                        tree.add(f"Original summed runtime: {humanize_runtime(original_code_baseline.runtime)}")
                        tree.add(
                            f"Best summed runtime: {humanize_runtime(candidate_result.best_test_runtime)} "
                            f"(measured over {candidate_result.max_loop_count} "
                            f"loop{'s' if candidate_result.max_loop_count > 1 else ''})"
                        )
                        tree.add(f"Speedup percentage: {perf_gain * 100:.1f}%")
                        tree.add(f"Speedup ratio: {perf_gain + 1:.3f}X")
                        if (
                            original_code_baseline.async_throughput is not None
                            and candidate_result.async_throughput is not None
                        ):
                            throughput_gain_value = throughput_gain(
                                original_throughput=original_code_baseline.async_throughput,
                                optimized_throughput=candidate_result.async_throughput,
                            )
                            tree.add(f"Original async throughput: {original_code_baseline.async_throughput} executions")
                            tree.add(f"Optimized async throughput: {candidate_result.async_throughput} executions")
                            tree.add(f"Throughput improvement: {throughput_gain_value * 100:.1f}%")
                        line_profile_test_results = self.line_profiler_step(
                            code_context=code_context,
                            original_helper_code=original_helper_code,
                            candidate_index=candidate_index,
                        )
                        optimized_line_profiler_results[candidate.optimization_id] = line_profile_test_results[
                            "str_out"
                        ]
                        replay_perf_gain = {}
                        if self.args.benchmark:
                            test_results_by_benchmark = candidate_result.benchmarking_test_results.group_by_benchmarks(
                                self.total_benchmark_timings.keys(), self.replay_tests_dir, self.project_root
                            )
                            if len(test_results_by_benchmark) > 0:
                                benchmark_tree = Tree("Speedup percentage on benchmarks:")
                            for benchmark_key, candidate_test_results in test_results_by_benchmark.items():
                                original_code_replay_runtime = original_code_baseline.replay_benchmarking_test_results[
                                    benchmark_key
                                ].total_passed_runtime()
                                candidate_replay_runtime = candidate_test_results.total_passed_runtime()
                                replay_perf_gain[benchmark_key] = performance_gain(
                                    original_runtime_ns=original_code_replay_runtime,
                                    optimized_runtime_ns=candidate_replay_runtime,
                                )
                                benchmark_tree.add(f"{benchmark_key}: {replay_perf_gain[benchmark_key] * 100:.1f}%")
                        best_optimization = BestOptimization(
                            candidate=candidate,
                            helper_functions=code_context.helper_functions,
                            code_context=code_context,
                            runtime=best_test_runtime,
                            line_profiler_test_results=line_profile_test_results,
                            winning_behavior_test_results=candidate_result.behavior_test_results,
                            replay_performance_gain=replay_perf_gain if self.args.benchmark else None,
                            winning_benchmarking_test_results=candidate_result.benchmarking_test_results,
                            winning_replay_benchmarking_test_results=candidate_result.benchmarking_test_results,
                            async_throughput=candidate_result.async_throughput,
                        )
                        valid_optimizations.append(best_optimization)
                        # queue corresponding refined optimization for best optimization
                        if not candidate.optimization_id.endswith("refi"):
                            future_all_refinements.append(
                                self.refine_optimizations(
                                    valid_optimizations=[best_optimization],
                                    original_code_baseline=original_code_baseline,
                                    code_context=code_context,
                                    trace_id=self.function_trace_id[:-4] + exp_type
                                    if self.experiment_id
                                    else self.function_trace_id,
                                    ai_service_client=ai_service_client,
                                    executor=self.executor,
                                )
                            )
                    else:
                        tree.add(
                            f"Summed runtime: {humanize_runtime(best_test_runtime)} "
                            f"(measured over {candidate_result.max_loop_count} "
                            f"loop{'s' if candidate_result.max_loop_count > 1 else ''})"
                        )
                        tree.add(f"Speedup percentage: {perf_gain * 100:.1f}%")
                        tree.add(f"Speedup ratio: {perf_gain + 1:.3f}X")
                        if (
                            original_code_baseline.async_throughput is not None
                            and candidate_result.async_throughput is not None
                        ):
                            throughput_gain_value = throughput_gain(
                                original_throughput=original_code_baseline.async_throughput,
                                optimized_throughput=candidate_result.async_throughput,
                            )
                            tree.add(f"Throughput gain: {throughput_gain_value * 100:.1f}%")

                    if is_LSP_enabled():
                        lsp_log(LspMarkdownMessage(markdown=tree_to_markdown(tree)))
                    else:
                        console.print(tree)
                    if self.args.benchmark and benchmark_tree:
                        console.print(benchmark_tree)
                    console.rule()
            except KeyboardInterrupt as e:
                logger.exception(f"Optimization interrupted: {e}")
                raise
            finally:
                # reset for the next candidate
                self.write_code_and_helpers(
                    self.function_to_optimize_source_code, original_helper_code, self.function_to_optimize.file_path
                )
        if not valid_optimizations:
            return None
        # need to figure out the best candidate here before we return best_optimization
        # reassign the shorter code here
        valid_candidates_with_shorter_code = []
        diff_lens_list = []  # character level diff
        speedups_list = []
        optimization_ids = []
        diff_strs = []
        runtimes_list = []
        for valid_opt in valid_optimizations:
            valid_opt_normalized_code = normalize_code(valid_opt.candidate.source_code.flat.strip())
            new_candidate_with_shorter_code = OptimizedCandidate(
                source_code=ast_code_to_id[valid_opt_normalized_code]["shorter_source_code"],
                optimization_id=valid_opt.candidate.optimization_id,
                explanation=valid_opt.candidate.explanation,
            )
            new_best_opt = BestOptimization(
                candidate=new_candidate_with_shorter_code,
                helper_functions=valid_opt.helper_functions,
                code_context=valid_opt.code_context,
                runtime=valid_opt.runtime,
                line_profiler_test_results=valid_opt.line_profiler_test_results,
                winning_behavior_test_results=valid_opt.winning_behavior_test_results,
                replay_performance_gain=valid_opt.replay_performance_gain,
                winning_benchmarking_test_results=valid_opt.winning_benchmarking_test_results,
                winning_replay_benchmarking_test_results=valid_opt.winning_replay_benchmarking_test_results,
                async_throughput=valid_opt.async_throughput,
            )
            valid_candidates_with_shorter_code.append(new_best_opt)
            diff_lens_list.append(
                diff_length(new_best_opt.candidate.source_code.flat, code_context.read_writable_code.flat)
            )  # char level diff
            diff_strs.append(
                unified_diff_strings(code_context.read_writable_code.flat, new_best_opt.candidate.source_code.flat)
            )
            speedups_list.append(
                1
                + performance_gain(
                    original_runtime_ns=original_code_baseline.runtime, optimized_runtime_ns=new_best_opt.runtime
                )
            )
            optimization_ids.append(new_best_opt.candidate.optimization_id)
            runtimes_list.append(new_best_opt.runtime)
        if len(optimization_ids) > 1:
            future_ranking = self.executor.submit(
                ai_service_client.generate_ranking,
                diffs=diff_strs,
                optimization_ids=optimization_ids,
                speedups=speedups_list,
                trace_id=self.function_trace_id[:-4] + exp_type if self.experiment_id else self.function_trace_id,
            )
            concurrent.futures.wait([future_ranking])
            ranking = future_ranking.result()
            if ranking:
                min_key = ranking[0]
            else:
                diff_lens_ranking = create_rank_dictionary_compact(diff_lens_list)
                runtimes_ranking = create_rank_dictionary_compact(runtimes_list)
                # TODO: better way to resolve conflicts with same min ranking
                overall_ranking = {key: diff_lens_ranking[key] + runtimes_ranking[key] for key in diff_lens_ranking}
                min_key = min(overall_ranking, key=overall_ranking.get)
        elif len(optimization_ids) == 1:
            min_key = 0  # only one candidate in valid _opts, already returns if there are no valid candidates
        else:  # 0? shouldn't happen but it's there to escape potential bugs
            return None
        best_optimization = valid_candidates_with_shorter_code[min_key]
        # reassign code string which is the shortest
        ai_service_client.log_results(
            function_trace_id=self.function_trace_id[:-4] + exp_type if self.experiment_id else self.function_trace_id,
            speedup_ratio=speedup_ratios,
            original_runtime=original_code_baseline.runtime,
            optimized_runtime=optimized_runtimes,
            is_correct=is_correct,
            optimized_line_profiler_results=optimized_line_profiler_results,
            optimizations_post=optimizations_post,
            metadata={"best_optimization_id": best_optimization.candidate.optimization_id},
        )
        return best_optimization

    def refine_optimizations(
        self,
        valid_optimizations: list[BestOptimization],
        original_code_baseline: OriginalCodeBaseline,
        code_context: CodeOptimizationContext,
        trace_id: str,
        ai_service_client: AiServiceClient,
        executor: concurrent.futures.ThreadPoolExecutor,
    ) -> concurrent.futures.Future:
        request = [
            AIServiceRefinerRequest(
                optimization_id=opt.candidate.optimization_id,
                original_source_code=code_context.read_writable_code.markdown,
                read_only_dependency_code=code_context.read_only_context_code,
                original_code_runtime=humanize_runtime(original_code_baseline.runtime),
                optimized_source_code=opt.candidate.source_code.markdown,
                optimized_explanation=opt.candidate.explanation,
                optimized_code_runtime=humanize_runtime(opt.runtime),
                speedup=f"{int(performance_gain(original_runtime_ns=original_code_baseline.runtime, optimized_runtime_ns=opt.runtime) * 100)}%",
                trace_id=trace_id,
                original_line_profiler_results=original_code_baseline.line_profile_results["str_out"],
                optimized_line_profiler_results=opt.line_profiler_test_results["str_out"],
            )
            for opt in valid_optimizations
        ]
        return executor.submit(ai_service_client.optimize_python_code_refinement, request=request)

    def log_successful_optimization(
        self, explanation: Explanation, generated_tests: GeneratedTestsList, exp_type: str
    ) -> None:
        if is_LSP_enabled():
            md_lines = [
                "### ⚡️ Optimization Summary",
                f"Function: `{self.function_to_optimize.qualified_name}`",
                f"File: `{explanation.file_path}`",
                f"Performance: {explanation.perf_improvement_line}",
                "",
                "#### Explanation\n",
                explanation.__str__(),
            ]

            optimization_summary_markdown = "\n".join(md_lines)
            tests_messages: list[LspCodeMessage] = []

            if generated_tests.generated_tests:
                tests_messages.extend(
                    [
                        LspCodeMessage(code=test.generated_original_test_source, file_name=f"test_{i + 1}.py")
                        for i, test in enumerate(generated_tests.generated_tests)
                    ]
                )

            logger.info("h3|Validated Tests")
            test_report = explanation.winning_behavior_test_results.get_test_pass_fail_report_by_type()
            test_report_md = report_to_markdown_table(test_report, "")

            # displaying tests summary
            lsp_log(LspMarkdownMessage(markdown=test_report_md))
            for test in tests_messages:
                lsp_log(test)

            # displaying optimization summary
            lsp_log(LspMarkdownMessage(markdown=optimization_summary_markdown))

        else:
            # normal console output
            explanation_panel = Panel(
                f"⚡️ Optimization successful! 📄 {self.function_to_optimize.qualified_name} in {explanation.file_path}\n"
                f"📈 {explanation.perf_improvement_line}\n"
                f"Explanation: \n{explanation.__str__()}",
                title="Optimization Summary",
                border_style="green",
            )

            if self.args.no_pr:
                tests_panel = Panel(
                    Syntax(
                        "\n".join([test.generated_original_test_source for test in generated_tests.generated_tests]),
                        "python",
                        line_numbers=True,
                    ),
                    title="Validated Tests",
                    border_style="blue",
                )

                console.print(Group(explanation_panel, tests_panel))
            else:
                console.print(explanation_panel)

        ph(
            "cli-optimize-success",
            {
                "function_trace_id": self.function_trace_id[:-4] + exp_type
                if self.experiment_id
                else self.function_trace_id,
                "speedup_x": explanation.speedup_x,
                "speedup_pct": explanation.speedup_pct,
                "best_runtime": explanation.best_runtime_ns,
                "original_runtime": explanation.original_runtime_ns,
                "winning_test_results": {
                    tt.to_name(): v
                    for tt, v in explanation.winning_behavior_test_results.get_test_pass_fail_report_by_type().items()
                },
            },
        )

    @staticmethod
    def write_code_and_helpers(original_code: str, original_helper_code: dict[Path, str], path: Path) -> None:
        with path.open("w", encoding="utf8") as f:
            f.write(original_code)
        for module_abspath, helper_code in original_helper_code.items():
            with Path(module_abspath).open("w", encoding="utf8") as f:
                f.write(helper_code)

    def reformat_code_and_helpers(
        self,
        helper_functions: list[FunctionSource],
        path: Path,
        original_code: str,
        optimized_context: CodeStringsMarkdown,
    ) -> tuple[str, dict[Path, str]]:
        should_sort_imports = not self.args.disable_imports_sorting
        if should_sort_imports and sort_imports(code=original_code) != original_code:
            should_sort_imports = False

        optimized_code = ""
        if optimized_context is not None:
            file_to_code_context = optimized_context.file_to_path()
            optimized_code = file_to_code_context.get(str(path.relative_to(self.project_root)), "")

        new_code = format_code(
            self.args.formatter_cmds, path, optimized_code=optimized_code, check_diff=True, exit_on_failure=False
        )
        if should_sort_imports:
            new_code = sort_imports(new_code)

        new_helper_code: dict[Path, str] = {}
        for hp in helper_functions:
            module_abspath = hp.file_path
            hp_source_code = hp.source_code
            formatted_helper_code = format_code(
                self.args.formatter_cmds,
                module_abspath,
                optimized_code=hp_source_code,
                check_diff=True,
                exit_on_failure=False,
            )
            if should_sort_imports:
                formatted_helper_code = sort_imports(formatted_helper_code)
            new_helper_code[module_abspath] = formatted_helper_code

        return new_code, new_helper_code

    def replace_function_and_helpers_with_optimized_code(
        self,
        code_context: CodeOptimizationContext,
        optimized_code: CodeStringsMarkdown,
        original_helper_code: dict[Path, str],
    ) -> bool:
        did_update = False
        read_writable_functions_by_file_path = defaultdict(set)
        read_writable_functions_by_file_path[self.function_to_optimize.file_path].add(
            self.function_to_optimize.qualified_name
        )
        for helper_function in code_context.helper_functions:
            if helper_function.jedi_definition.type != "class":
                read_writable_functions_by_file_path[helper_function.file_path].add(helper_function.qualified_name)
        for module_abspath, qualified_names in read_writable_functions_by_file_path.items():
            did_update |= replace_function_definitions_in_module(
                function_names=list(qualified_names),
                optimized_code=optimized_code,
                module_abspath=module_abspath,
                preexisting_objects=code_context.preexisting_objects,
                project_root_path=self.project_root,
            )
        unused_helpers = detect_unused_helper_functions(self.function_to_optimize, code_context, optimized_code)

        # Revert unused helper functions to their original definitions
        if unused_helpers:
            revert_unused_helper_functions(self.project_root, unused_helpers, original_helper_code)

        return did_update

    def get_code_optimization_context(self) -> Result[CodeOptimizationContext, str]:
        try:
            new_code_ctx = code_context_extractor.get_code_optimization_context(
                self.function_to_optimize, self.project_root
            )
        except ValueError as e:
            return Failure(str(e))

        return Success(
            CodeOptimizationContext(
                testgen_context=new_code_ctx.testgen_context,
                read_writable_code=new_code_ctx.read_writable_code,
                read_only_context_code=new_code_ctx.read_only_context_code,
                hashing_code_context=new_code_ctx.hashing_code_context,
                hashing_code_context_hash=new_code_ctx.hashing_code_context_hash,
                helper_functions=new_code_ctx.helper_functions,  # only functions that are read writable
                preexisting_objects=new_code_ctx.preexisting_objects,
            )
        )

    @staticmethod
    def cleanup_leftover_test_return_values() -> None:
        # remove leftovers from previous run
        get_run_tmp_file(Path("test_return_values_0.bin")).unlink(missing_ok=True)
        get_run_tmp_file(Path("test_return_values_0.sqlite")).unlink(missing_ok=True)

    def instrument_existing_tests(self, function_to_all_tests: dict[str, set[FunctionCalledInTest]]) -> set[Path]:
        existing_test_files_count = 0
        replay_test_files_count = 0
        concolic_coverage_test_files_count = 0
        unique_instrumented_test_files = set()

        func_qualname = self.function_to_optimize.qualified_name_with_modules_from_root(self.project_root)
        if func_qualname not in function_to_all_tests:
            logger.info(f"Did not find any pre-existing tests for '{func_qualname}', will only use generated tests.")
            console.rule()
        else:
            test_file_invocation_positions = defaultdict(list)
            for tests_in_file in function_to_all_tests.get(func_qualname):
                test_file_invocation_positions[
                    (tests_in_file.tests_in_file.test_file, tests_in_file.tests_in_file.test_type)
                ].append(tests_in_file)
            for (test_file, test_type), tests_in_file_list in test_file_invocation_positions.items():
                path_obj_test_file = Path(test_file)
                if test_type == TestType.EXISTING_UNIT_TEST:
                    existing_test_files_count += 1
                elif test_type == TestType.REPLAY_TEST:
                    replay_test_files_count += 1
                elif test_type == TestType.CONCOLIC_COVERAGE_TEST:
                    concolic_coverage_test_files_count += 1
                else:
                    msg = f"Unexpected test type: {test_type}"
                    raise ValueError(msg)
                success, injected_behavior_test = inject_profiling_into_existing_test(
                    mode=TestingMode.BEHAVIOR,
                    test_path=path_obj_test_file,
                    call_positions=[test.position for test in tests_in_file_list],
                    function_to_optimize=self.function_to_optimize,
                    tests_project_root=self.test_cfg.tests_project_rootdir,
                    test_framework=self.args.test_framework,
                )
                if not success:
                    continue
                success, injected_perf_test = inject_profiling_into_existing_test(
                    mode=TestingMode.PERFORMANCE,
                    test_path=path_obj_test_file,
                    call_positions=[test.position for test in tests_in_file_list],
                    function_to_optimize=self.function_to_optimize,
                    tests_project_root=self.test_cfg.tests_project_rootdir,
                    test_framework=self.args.test_framework,
                )
                if not success:
                    continue
                # TODO: this naming logic should be moved to a function and made more standard
                new_behavioral_test_path = Path(
                    f"{os.path.splitext(test_file)[0]}__perfinstrumented{os.path.splitext(test_file)[1]}"  # noqa: PTH122
                )
                new_perf_test_path = Path(
                    f"{os.path.splitext(test_file)[0]}__perfonlyinstrumented{os.path.splitext(test_file)[1]}"  # noqa: PTH122
                )
                if injected_behavior_test is not None:
                    with new_behavioral_test_path.open("w", encoding="utf8") as _f:
                        _f.write(injected_behavior_test)
                else:
                    msg = "injected_behavior_test is None"
                    raise ValueError(msg)
                if injected_perf_test is not None:
                    with new_perf_test_path.open("w", encoding="utf8") as _f:
                        _f.write(injected_perf_test)

                unique_instrumented_test_files.add(new_behavioral_test_path)
                unique_instrumented_test_files.add(new_perf_test_path)

                if not self.test_files.get_by_original_file_path(path_obj_test_file):
                    self.test_files.add(
                        TestFile(
                            instrumented_behavior_file_path=new_behavioral_test_path,
                            benchmarking_file_path=new_perf_test_path,
                            original_source=None,
                            original_file_path=Path(test_file),
                            test_type=test_type,
                            tests_in_file=[t.tests_in_file for t in tests_in_file_list],
                        )
                    )

            logger.info(
                f"Discovered {existing_test_files_count} existing unit test file"
                f"{'s' if existing_test_files_count != 1 else ''}, {replay_test_files_count} replay test file"
                f"{'s' if replay_test_files_count != 1 else ''}, and "
                f"{concolic_coverage_test_files_count} concolic coverage test file"
                f"{'s' if concolic_coverage_test_files_count != 1 else ''} for {func_qualname}"
            )
            console.rule()
        return unique_instrumented_test_files

    def generate_tests_and_optimizations(
        self,
        testgen_context: CodeStringsMarkdown,
        read_writable_code: CodeStringsMarkdown,
        read_only_context_code: str,
        helper_functions: list[FunctionSource],
        generated_test_paths: list[Path],
        generated_perf_test_paths: list[Path],
        run_experiment: bool = False,  # noqa: FBT001, FBT002
    ) -> Result[tuple[GeneratedTestsList, dict[str, set[FunctionCalledInTest]], OptimizationSet], str]:
        n_tests = N_TESTS_TO_GENERATE_EFFECTIVE
        assert len(generated_test_paths) == n_tests
        console.rule()
        # Submit the test generation task as future
        future_tests = self.submit_test_generation_tasks(
            self.executor,
            testgen_context.markdown,
            [definition.fully_qualified_name for definition in helper_functions],
            generated_test_paths,
            generated_perf_test_paths,
        )
        n_candidates = N_CANDIDATES_EFFECTIVE
        future_optimization_candidates = self.executor.submit(
            self.aiservice_client.optimize_python_code,
            read_writable_code.markdown,
            read_only_context_code,
            self.function_trace_id[:-4] + "EXP0" if run_experiment else self.function_trace_id,
            n_candidates,
            ExperimentMetadata(id=self.experiment_id, group="control") if run_experiment else None,
            is_async=self.function_to_optimize.is_async,
        )
        future_candidates_exp = None

        future_concolic_tests = self.executor.submit(
            generate_concolic_tests, self.test_cfg, self.args, self.function_to_optimize, self.function_to_optimize_ast
        )
        futures = [*future_tests, future_optimization_candidates, future_concolic_tests]
        if run_experiment:
            future_candidates_exp = self.executor.submit(
                self.local_aiservice_client.optimize_python_code,
                read_writable_code.markdown,
                read_only_context_code,
                self.function_trace_id[:-4] + "EXP1",
                n_candidates,
                ExperimentMetadata(id=self.experiment_id, group="experiment"),
                is_async=self.function_to_optimize.is_async,
            )
            futures.append(future_candidates_exp)

        # Wait for all futures to complete
        concurrent.futures.wait(futures)

        # Retrieve results
        candidates: list[OptimizedCandidate] = future_optimization_candidates.result()
        logger.info(f"lsp|Generated '{len(candidates)}' candidate optimizations.")
        console.rule()

        if not candidates:
            return Failure(f"/!\\ NO OPTIMIZATIONS GENERATED for {self.function_to_optimize.function_name}")

        candidates_experiment = future_candidates_exp.result() if future_candidates_exp else None

        # Process test generation results

        tests: list[GeneratedTests] = []
        for future in future_tests:
            res = future.result()
            if res:
                (
                    generated_test_source,
                    instrumented_behavior_test_source,
                    instrumented_perf_test_source,
                    test_behavior_path,
                    test_perf_path,
                ) = res
                tests.append(
                    GeneratedTests(
                        generated_original_test_source=generated_test_source,
                        instrumented_behavior_test_source=instrumented_behavior_test_source,
                        instrumented_perf_test_source=instrumented_perf_test_source,
                        behavior_file_path=test_behavior_path,
                        perf_file_path=test_perf_path,
                    )
                )
        if not tests:
            logger.warning(f"Failed to generate and instrument tests for {self.function_to_optimize.function_name}")
            return Failure(f"/!\\ NO TESTS GENERATED for {self.function_to_optimize.function_name}")
        function_to_concolic_tests, concolic_test_str = future_concolic_tests.result()

        count_tests = len(tests)
        if concolic_test_str:
            count_tests += 1

        logger.info(f"Generated '{count_tests}' tests for {self.function_to_optimize.function_name}")
        console.rule()
        generated_tests = GeneratedTestsList(generated_tests=tests)
        result = (
            count_tests,
            generated_tests,
            function_to_concolic_tests,
            concolic_test_str,
            OptimizationSet(control=candidates, experiment=candidates_experiment),
        )
        self.generate_and_instrument_tests_results = result
        return Success(result)

    def setup_and_establish_baseline(
        self,
        code_context: CodeOptimizationContext,
        original_helper_code: dict[Path, str],
        function_to_concolic_tests: dict[str, set[FunctionCalledInTest]],
        generated_test_paths: list[Path],
        generated_perf_test_paths: list[Path],
        instrumented_unittests_created_for_function: set[Path],
        original_conftest_content: str | None,
    ) -> Result[
        tuple[str, dict[str, set[FunctionCalledInTest]], OriginalCodeBaseline, list[str], dict[Path, set[str]]], str
    ]:
        """Set up baseline context and establish original code baseline."""
        function_to_optimize_qualified_name = self.function_to_optimize.qualified_name
        function_to_all_tests = {
            key: self.function_to_tests.get(key, set()) | function_to_concolic_tests.get(key, set())
            for key in set(self.function_to_tests) | set(function_to_concolic_tests)
        }

        # Get a dict of file_path_to_classes of fto and helpers_of_fto
        file_path_to_helper_classes = defaultdict(set)
        for function_source in code_context.helper_functions:
            if (
                function_source.qualified_name != self.function_to_optimize.qualified_name
                and "." in function_source.qualified_name
            ):
                file_path_to_helper_classes[function_source.file_path].add(function_source.qualified_name.split(".")[0])

        baseline_result = self.establish_original_code_baseline(
            code_context=code_context,
            original_helper_code=original_helper_code,
            file_path_to_helper_classes=file_path_to_helper_classes,
        )

        console.rule()
        paths_to_cleanup = (
            generated_test_paths + generated_perf_test_paths + list(instrumented_unittests_created_for_function)
        )

        if not is_successful(baseline_result):
            if self.args.override_fixtures:
                restore_conftest(original_conftest_content)
            cleanup_paths(paths_to_cleanup)
            return Failure(baseline_result.failure())

        original_code_baseline, test_functions_to_remove = baseline_result.unwrap()
        if isinstance(original_code_baseline, OriginalCodeBaseline) and (
            not coverage_critic(original_code_baseline.coverage_results, self.args.test_framework)
            or not quantity_of_tests_critic(original_code_baseline)
        ):
            if self.args.override_fixtures:
                restore_conftest(original_conftest_content)
            cleanup_paths(paths_to_cleanup)
            return Failure("The threshold for test confidence was not met.")

        return Success(
            (
                function_to_optimize_qualified_name,
                function_to_all_tests,
                original_code_baseline,
                test_functions_to_remove,
                file_path_to_helper_classes,
            )
        )

    def find_and_process_best_optimization(
        self,
        optimizations_set: OptimizationSet,
        code_context: CodeOptimizationContext,
        original_code_baseline: OriginalCodeBaseline,
        original_helper_code: dict[Path, str],
        file_path_to_helper_classes: dict[Path, set[str]],
        function_to_optimize_qualified_name: str,
        function_to_all_tests: dict[str, set[FunctionCalledInTest]],
        generated_tests: GeneratedTestsList,
        test_functions_to_remove: list[str],
        concolic_test_str: str | None,
    ) -> BestOptimization | None:
        """Find the best optimization candidate and process it with all required steps."""
        best_optimization = None
        for _u, (candidates, exp_type) in enumerate(
            zip([optimizations_set.control, optimizations_set.experiment], ["EXP0", "EXP1"])
        ):
            if candidates is None:
                continue

            best_optimization = self.determine_best_candidate(
                candidates=candidates,
                code_context=code_context,
                original_code_baseline=original_code_baseline,
                original_helper_code=original_helper_code,
                file_path_to_helper_classes=file_path_to_helper_classes,
                exp_type=exp_type,
            )
            ph(
                "cli-optimize-function-finished",
                {
                    "function_trace_id": self.function_trace_id[:-4] + exp_type
                    if self.experiment_id
                    else self.function_trace_id
                },
            )

            if best_optimization:
                logger.info("h2|Best candidate 🚀")
                code_print(
                    best_optimization.candidate.source_code.flat,
                    file_name="best_candidate.py",
                    function_name=self.function_to_optimize.function_name,
                )
                processed_benchmark_info = None
                if self.args.benchmark:
                    processed_benchmark_info = process_benchmark_data(
                        replay_performance_gain=best_optimization.replay_performance_gain,
                        fto_benchmark_timings=self.function_benchmark_timings,
                        total_benchmark_timings=self.total_benchmark_timings,
                    )
                explanation = Explanation(
                    raw_explanation_message=best_optimization.candidate.explanation,
                    winning_behavior_test_results=best_optimization.winning_behavior_test_results,
                    winning_benchmarking_test_results=best_optimization.winning_benchmarking_test_results,
                    original_runtime_ns=original_code_baseline.runtime,
                    best_runtime_ns=best_optimization.runtime,
                    function_name=function_to_optimize_qualified_name,
                    file_path=self.function_to_optimize.file_path,
                    benchmark_details=processed_benchmark_info.benchmark_details if processed_benchmark_info else None,
                    original_async_throughput=original_code_baseline.async_throughput,
                    best_async_throughput=best_optimization.async_throughput,
                )

                self.replace_function_and_helpers_with_optimized_code(
                    code_context=code_context,
                    optimized_code=best_optimization.candidate.source_code,
                    original_helper_code=original_helper_code,
                )

                new_code, new_helper_code = self.reformat_code_and_helpers(
                    code_context.helper_functions,
                    explanation.file_path,
                    self.function_to_optimize_source_code,
                    optimized_context=best_optimization.candidate.source_code,
                )

                original_code_combined = original_helper_code.copy()
                original_code_combined[explanation.file_path] = self.function_to_optimize_source_code
                new_code_combined = new_helper_code.copy()
                new_code_combined[explanation.file_path] = new_code
                self.process_review(
                    original_code_baseline,
                    best_optimization,
                    generated_tests,
                    test_functions_to_remove,
                    concolic_test_str,
                    original_code_combined,
                    new_code_combined,
                    explanation,
                    function_to_all_tests,
                    exp_type,
                    original_helper_code,
                    code_context,
                )
        return best_optimization

    def process_review(
        self,
        original_code_baseline: OriginalCodeBaseline,
        best_optimization: BestOptimization,
        generated_tests: GeneratedTestsList,
        test_functions_to_remove: list[str],
        concolic_test_str: str | None,
        original_code_combined: dict[Path, str],
        new_code_combined: dict[Path, str],
        explanation: Explanation,
        function_to_all_tests: dict[str, set[FunctionCalledInTest]],
        exp_type: str,
        original_helper_code: dict[Path, str],
        code_context: CodeOptimizationContext,
    ) -> None:
        coverage_message = (
            original_code_baseline.coverage_results.build_message()
            if original_code_baseline.coverage_results
            else "Coverage data not available"
        )

        generated_tests = remove_functions_from_generated_tests(
            generated_tests=generated_tests, test_functions_to_remove=test_functions_to_remove
        )

        original_runtime_by_test = original_code_baseline.benchmarking_test_results.usable_runtime_data_by_test_case()
        optimized_runtime_by_test = (
            best_optimization.winning_benchmarking_test_results.usable_runtime_data_by_test_case()
        )

        generated_tests = add_runtime_comments_to_generated_tests(
            generated_tests, original_runtime_by_test, optimized_runtime_by_test
        )

        generated_tests_str = "\n#------------------------------------------------\n".join(
            [test.generated_original_test_source for test in generated_tests.generated_tests]
        )
        if concolic_test_str:
            generated_tests_str += "\n#------------------------------------------------\n" + concolic_test_str

        existing_tests, replay_tests, concolic_tests = existing_tests_source_for(
            self.function_to_optimize.qualified_name_with_modules_from_root(self.project_root),
            function_to_all_tests,
            test_cfg=self.test_cfg,
            original_runtimes_all=original_runtime_by_test,
            optimized_runtimes_all=optimized_runtime_by_test,
        )
        original_throughput_str = None
        optimized_throughput_str = None
        throughput_improvement_str = None

        if (
            self.function_to_optimize.is_async
            and original_code_baseline.async_throughput is not None
            and best_optimization.async_throughput is not None
        ):
            original_throughput_str = f"{original_code_baseline.async_throughput} operations/second"
            optimized_throughput_str = f"{best_optimization.async_throughput} operations/second"
            throughput_improvement_value = throughput_gain(
                original_throughput=original_code_baseline.async_throughput,
                optimized_throughput=best_optimization.async_throughput,
            )
            throughput_improvement_str = f"{throughput_improvement_value * 100:.1f}%"

        new_explanation_raw_str = self.aiservice_client.get_new_explanation(
            source_code=code_context.read_writable_code.flat,
            dependency_code=code_context.read_only_context_code,
            trace_id=self.function_trace_id[:-4] + exp_type if self.experiment_id else self.function_trace_id,
            optimized_code=best_optimization.candidate.source_code.flat,
            original_line_profiler_results=original_code_baseline.line_profile_results["str_out"],
            optimized_line_profiler_results=best_optimization.line_profiler_test_results["str_out"],
            original_code_runtime=humanize_runtime(original_code_baseline.runtime),
            optimized_code_runtime=humanize_runtime(best_optimization.runtime),
            speedup=f"{int(performance_gain(original_runtime_ns=original_code_baseline.runtime, optimized_runtime_ns=best_optimization.runtime) * 100)}%",
            annotated_tests=generated_tests_str,
            optimization_id=best_optimization.candidate.optimization_id,
            original_explanation=best_optimization.candidate.explanation,
            original_throughput=original_throughput_str,
            optimized_throughput=optimized_throughput_str,
            throughput_improvement=throughput_improvement_str,
        )
        new_explanation = Explanation(
            raw_explanation_message=new_explanation_raw_str or explanation.raw_explanation_message,
            winning_behavior_test_results=explanation.winning_behavior_test_results,
            winning_benchmarking_test_results=explanation.winning_benchmarking_test_results,
            original_runtime_ns=explanation.original_runtime_ns,
            best_runtime_ns=explanation.best_runtime_ns,
            function_name=explanation.function_name,
            file_path=explanation.file_path,
            benchmark_details=explanation.benchmark_details,
            original_async_throughput=explanation.original_async_throughput,
            best_async_throughput=explanation.best_async_throughput,
        )
        self.log_successful_optimization(new_explanation, generated_tests, exp_type)

        best_optimization.explanation_v2 = new_explanation.explanation_message()

        data = {
            "original_code": original_code_combined,
            "new_code": new_code_combined,
            "explanation": new_explanation,
            "existing_tests_source": existing_tests,
            "generated_original_test_source": generated_tests_str,
            "function_trace_id": self.function_trace_id[:-4] + exp_type
            if self.experiment_id
            else self.function_trace_id,
            "coverage_message": coverage_message,
            "replay_tests": replay_tests,
            "concolic_tests": concolic_tests,
        }

        raise_pr = not self.args.no_pr
        staging_review = self.args.staging_review

        if raise_pr or staging_review:
            data["root_dir"] = git_root_dir()
            calling_fn_details = get_opt_review_metrics(
                self.function_to_optimize_source_code,
                self.function_to_optimize.file_path,
                self.function_to_optimize.qualified_name,
                self.project_root,
                self.test_cfg.tests_root,
            )
            opt_review_response = ""
            try:
                opt_review_response = self.aiservice_client.get_optimization_review(
                    **data, calling_fn_details=calling_fn_details
                )
            except Exception as e:
                logger.debug(f"optimization review response failed, investigate {e}")
            data["optimization_review"] = opt_review_response
        if raise_pr and not staging_review:
            data["git_remote"] = self.args.git_remote
            check_create_pr(**data)
        elif staging_review:
            response = create_staging(**data)
            if response.status_code == 200:
                trace_id = self.function_trace_id[:-4] + exp_type if self.experiment_id else self.function_trace_id
                staging_url = f"{CFWEBAPP_BASE_URL}/review-optimizations/{trace_id}"
                console.print(
                    Panel(
                        f"[bold green]✅ Staging created:[/bold green]\n[link={staging_url}]{staging_url}[/link]",
                        title="Staging Link",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"[bold red]❌ Failed to create staging[/bold red]\nStatus: {response.status_code}",
                        title="Staging Error",
                        border_style="red",
                    )
                )

        else:
            # Mark optimization success since no PR will be created
            mark_optimization_success(
                trace_id=self.function_trace_id, is_optimization_found=best_optimization is not None
            )

        # If worktree mode, do not revert code and helpers,, otherwise we would have an empty diff when writing the patch in the lsp
        if self.args.worktree:
            return

        if raise_pr and (
            self.args.all
            or env_utils.get_pr_number()
            or self.args.replay_test
            or (self.args.file and not self.args.function)
        ):
            self.revert_code_and_helpers(original_helper_code)
            return

        if staging_review:
            # always revert code and helpers when staging review
            self.revert_code_and_helpers(original_helper_code)
            return

    def revert_code_and_helpers(self, original_helper_code: dict[Path, str]) -> None:
        logger.info("Reverting code and helpers...")
        self.write_code_and_helpers(
            self.function_to_optimize_source_code, original_helper_code, self.function_to_optimize.file_path
        )

    def establish_original_code_baseline(
        self,
        code_context: CodeOptimizationContext,
        original_helper_code: dict[Path, str],
        file_path_to_helper_classes: dict[Path, set[str]],
    ) -> Result[tuple[OriginalCodeBaseline, list[str]], str]:
        line_profile_results = {"timings": {}, "unit": 0, "str_out": ""}
        # For the original function - run the tests and get the runtime, plus coverage
        assert (test_framework := self.args.test_framework) in {"pytest", "unittest"}  # noqa: RUF018
        success = True

        test_env = self.get_test_env(codeflash_loop_index=0, codeflash_test_iteration=0, codeflash_tracer_disable=1)

        if self.function_to_optimize.is_async:
            from codeflash.code_utils.instrument_existing_tests import instrument_source_module_with_async_decorators

            success, instrumented_source = instrument_source_module_with_async_decorators(
                self.function_to_optimize.file_path, self.function_to_optimize, TestingMode.BEHAVIOR
            )
            if success and instrumented_source:
                with self.function_to_optimize.file_path.open("w", encoding="utf8") as f:
                    f.write(instrumented_source)
                logger.debug(f"Applied async instrumentation to {self.function_to_optimize.file_path}")

        # Instrument codeflash capture
        with progress_bar("Running tests to establish original code behavior..."):
            try:
                instrument_codeflash_capture(
                    self.function_to_optimize, file_path_to_helper_classes, self.test_cfg.tests_root
                )
                total_looping_time = TOTAL_LOOPING_TIME_EFFECTIVE
                behavioral_results, coverage_results = self.run_and_parse_tests(
                    testing_type=TestingMode.BEHAVIOR,
                    test_env=test_env,
                    test_files=self.test_files,
                    optimization_iteration=0,
                    testing_time=total_looping_time,
                    enable_coverage=test_framework == "pytest",
                    code_context=code_context,
                )
            finally:
                # Remove codeflash capture
                self.write_code_and_helpers(
                    self.function_to_optimize_source_code, original_helper_code, self.function_to_optimize.file_path
                )
        if not behavioral_results:
            logger.warning(
                f"force_lsp|Couldn't run any tests for original function {self.function_to_optimize.function_name}. SKIPPING OPTIMIZING THIS FUNCTION."
            )
            console.rule()
            return Failure("Failed to establish a baseline for the original code - bevhavioral tests failed.")
        if not coverage_critic(coverage_results, self.args.test_framework):
            return Failure(
                f"Test coverage is {coverage_results.coverage}%, which is below the required threshold of {COVERAGE_THRESHOLD}%."
            )

        if test_framework == "pytest":
            with progress_bar("Running line profiling to identify performance bottlenecks..."):
                line_profile_results = self.line_profiler_step(
                    code_context=code_context, original_helper_code=original_helper_code, candidate_index=0
                )
            console.rule()
            with progress_bar("Running performance benchmarks..."):
                if self.function_to_optimize.is_async:
                    from codeflash.code_utils.instrument_existing_tests import (
                        instrument_source_module_with_async_decorators,
                    )

                    success, instrumented_source = instrument_source_module_with_async_decorators(
                        self.function_to_optimize.file_path, self.function_to_optimize, TestingMode.PERFORMANCE
                    )
                    if success and instrumented_source:
                        with self.function_to_optimize.file_path.open("w", encoding="utf8") as f:
                            f.write(instrumented_source)
                        logger.debug(
                            f"Applied async performance instrumentation to {self.function_to_optimize.file_path}"
                        )

                try:
                    benchmarking_results, _ = self.run_and_parse_tests(
                        testing_type=TestingMode.PERFORMANCE,
                        test_env=test_env,
                        test_files=self.test_files,
                        optimization_iteration=0,
                        testing_time=total_looping_time,
                        enable_coverage=False,
                        code_context=code_context,
                    )
                finally:
                    if self.function_to_optimize.is_async:
                        self.write_code_and_helpers(
                            self.function_to_optimize_source_code,
                            original_helper_code,
                            self.function_to_optimize.file_path,
                        )
        else:
            benchmarking_results = TestResults()
            start_time: float = time.time()
            for i in range(100):
                if i >= 5 and time.time() - start_time >= total_looping_time * 1.5:
                    # * 1.5 to give unittest a bit more time to run
                    break
                test_env["CODEFLASH_LOOP_INDEX"] = str(i + 1)
                with progress_bar("Running performance benchmarks..."):
                    unittest_loop_results, _ = self.run_and_parse_tests(
                        testing_type=TestingMode.PERFORMANCE,
                        test_env=test_env,
                        test_files=self.test_files,
                        optimization_iteration=0,
                        testing_time=total_looping_time,
                        enable_coverage=False,
                        code_context=code_context,
                        unittest_loop_index=i + 1,
                    )
                    benchmarking_results.merge(unittest_loop_results)

        console.print(
            TestResults.report_to_tree(
                behavioral_results.get_test_pass_fail_report_by_type(), title="Overall test results for original code"
            )
        )
        console.rule()

        total_timing = benchmarking_results.total_passed_runtime()  # caution: doesn't handle the loop index
        functions_to_remove = [
            result.id.test_function_name
            for result in behavioral_results
            if (result.test_type == TestType.GENERATED_REGRESSION and not result.did_pass)
        ]
        if total_timing == 0:
            logger.warning("The overall summed benchmark runtime of the original function is 0, couldn't run tests.")
            console.rule()
            success = False
        if not total_timing:
            logger.warning("Failed to run the tests for the original function, skipping optimization")
            console.rule()
            success = False
        if not success:
            return Failure("Failed to establish a baseline for the original code.")

        loop_count = max([int(result.loop_index) for result in benchmarking_results.test_results])
        logger.info(
            f"h3|⌚ Original code summed runtime measured over '{loop_count}' loop{'s' if loop_count > 1 else ''}: "
            f"'{humanize_runtime(total_timing)}' per full loop"
        )
        console.rule()
        logger.debug(f"Total original code runtime (ns): {total_timing}")

        async_throughput = None
        if self.function_to_optimize.is_async:
            async_throughput = calculate_function_throughput_from_test_results(
                benchmarking_results, self.function_to_optimize.function_name
            )
            logger.debug(f"Original async function throughput: {async_throughput} calls/second")
            console.rule()

        if self.args.benchmark:
            replay_benchmarking_test_results = benchmarking_results.group_by_benchmarks(
                self.total_benchmark_timings.keys(), self.replay_tests_dir, self.project_root
            )
        return Success(
            (
                OriginalCodeBaseline(
                    behavior_test_results=behavioral_results,
                    benchmarking_test_results=benchmarking_results,
                    replay_benchmarking_test_results=replay_benchmarking_test_results if self.args.benchmark else None,
                    runtime=total_timing,
                    coverage_results=coverage_results,
                    line_profile_results=line_profile_results,
                    async_throughput=async_throughput,
                ),
                functions_to_remove,
            )
        )

    def run_optimized_candidate(
        self,
        *,
        optimization_candidate_index: int,
        baseline_results: OriginalCodeBaseline,
        original_helper_code: dict[Path, str],
        file_path_to_helper_classes: dict[Path, set[str]],
    ) -> Result[OptimizedCandidateResult, str]:
        assert (test_framework := self.args.test_framework) in {"pytest", "unittest"}  # noqa: RUF018

        with progress_bar("Testing optimization candidate"):
            test_env = self.get_test_env(
                codeflash_loop_index=0,
                codeflash_test_iteration=optimization_candidate_index,
                codeflash_tracer_disable=1,
            )

            get_run_tmp_file(Path(f"test_return_values_{optimization_candidate_index}.sqlite")).unlink(missing_ok=True)
            # Instrument codeflash capture
            candidate_fto_code = Path(self.function_to_optimize.file_path).read_text("utf-8")
            candidate_helper_code = {}
            for module_abspath in original_helper_code:
                candidate_helper_code[module_abspath] = Path(module_abspath).read_text("utf-8")
            if self.function_to_optimize.is_async:
                from codeflash.code_utils.instrument_existing_tests import (
                    instrument_source_module_with_async_decorators,
                )

                success, instrumented_source = instrument_source_module_with_async_decorators(
                    self.function_to_optimize.file_path, self.function_to_optimize, TestingMode.BEHAVIOR
                )
                if success and instrumented_source:
                    with self.function_to_optimize.file_path.open("w", encoding="utf8") as f:
                        f.write(instrumented_source)
                    logger.debug(
                        f"Applied async behavioral instrumentation to {self.function_to_optimize.file_path} for candidate {optimization_candidate_index}"
                    )

            try:
                instrument_codeflash_capture(
                    self.function_to_optimize, file_path_to_helper_classes, self.test_cfg.tests_root
                )

                total_looping_time = TOTAL_LOOPING_TIME_EFFECTIVE
                candidate_behavior_results, _ = self.run_and_parse_tests(
                    testing_type=TestingMode.BEHAVIOR,
                    test_env=test_env,
                    test_files=self.test_files,
                    optimization_iteration=optimization_candidate_index,
                    testing_time=total_looping_time,
                    enable_coverage=False,
                )
            # Remove instrumentation
            finally:
                self.write_code_and_helpers(
                    candidate_fto_code, candidate_helper_code, self.function_to_optimize.file_path
                )
            console.print(
                TestResults.report_to_tree(
                    candidate_behavior_results.get_test_pass_fail_report_by_type(),
                    title=f"Behavioral Test Results for candidate {optimization_candidate_index}",
                )
            )
            console.rule()
            if compare_test_results(baseline_results.behavior_test_results, candidate_behavior_results):
                logger.info("h3|Test results matched ✅")
                console.rule()
            else:
                logger.info("h4|Test results did not match the test results of the original code ❌")
                console.rule()
                return Failure("Test results did not match the test results of the original code.")

            logger.info(f"loading|Running performance tests for candidate {optimization_candidate_index}...")

            if test_framework == "pytest":
                # For async functions, instrument at definition site for performance benchmarking
                if self.function_to_optimize.is_async:
                    from codeflash.code_utils.instrument_existing_tests import (
                        instrument_source_module_with_async_decorators,
                    )

                    success, instrumented_source = instrument_source_module_with_async_decorators(
                        self.function_to_optimize.file_path, self.function_to_optimize, TestingMode.PERFORMANCE
                    )
                    if success and instrumented_source:
                        with self.function_to_optimize.file_path.open("w", encoding="utf8") as f:
                            f.write(instrumented_source)
                        logger.debug(
                            f"Applied async performance instrumentation to {self.function_to_optimize.file_path} for candidate {optimization_candidate_index}"
                        )

                try:
                    candidate_benchmarking_results, _ = self.run_and_parse_tests(
                        testing_type=TestingMode.PERFORMANCE,
                        test_env=test_env,
                        test_files=self.test_files,
                        optimization_iteration=optimization_candidate_index,
                        testing_time=total_looping_time,
                        enable_coverage=False,
                    )
                finally:
                    # Restore original source if we instrumented it
                    if self.function_to_optimize.is_async:
                        self.write_code_and_helpers(
                            candidate_fto_code, candidate_helper_code, self.function_to_optimize.file_path
                        )
                loop_count = (
                    max(all_loop_indices)
                    if (
                        all_loop_indices := {
                            result.loop_index for result in candidate_benchmarking_results.test_results
                        }
                    )
                    else 0
                )

            else:
                candidate_benchmarking_results = TestResults()
                start_time: float = time.time()
                loop_count = 0
                for i in range(100):
                    if i >= 5 and time.time() - start_time >= TOTAL_LOOPING_TIME_EFFECTIVE * 1.5:
                        # * 1.5 to give unittest a bit more time to run
                        break
                    test_env["CODEFLASH_LOOP_INDEX"] = str(i + 1)
                    unittest_loop_results, _cov = self.run_and_parse_tests(
                        testing_type=TestingMode.PERFORMANCE,
                        test_env=test_env,
                        test_files=self.test_files,
                        optimization_iteration=optimization_candidate_index,
                        testing_time=TOTAL_LOOPING_TIME_EFFECTIVE,
                        unittest_loop_index=i + 1,
                    )
                    loop_count = i + 1
                    candidate_benchmarking_results.merge(unittest_loop_results)

            if (total_candidate_timing := candidate_benchmarking_results.total_passed_runtime()) == 0:
                logger.warning("The overall test runtime of the optimized function is 0, couldn't run tests.")
                console.rule()

            logger.debug(f"Total optimized code {optimization_candidate_index} runtime (ns): {total_candidate_timing}")

            candidate_async_throughput = None
            if self.function_to_optimize.is_async:
                candidate_async_throughput = calculate_function_throughput_from_test_results(
                    candidate_benchmarking_results, self.function_to_optimize.function_name
                )
                logger.debug(f"Candidate async function throughput: {candidate_async_throughput} calls/second")

            if self.args.benchmark:
                candidate_replay_benchmarking_results = candidate_benchmarking_results.group_by_benchmarks(
                    self.total_benchmark_timings.keys(), self.replay_tests_dir, self.project_root
                )
                for benchmark_name, benchmark_results in candidate_replay_benchmarking_results.items():
                    logger.debug(
                        f"Benchmark {benchmark_name} runtime (ns): {humanize_runtime(benchmark_results.total_passed_runtime())}"
                    )
            return Success(
                OptimizedCandidateResult(
                    max_loop_count=loop_count,
                    best_test_runtime=total_candidate_timing,
                    behavior_test_results=candidate_behavior_results,
                    benchmarking_test_results=candidate_benchmarking_results,
                    replay_benchmarking_test_results=candidate_replay_benchmarking_results
                    if self.args.benchmark
                    else None,
                    optimization_candidate_index=optimization_candidate_index,
                    total_candidate_timing=total_candidate_timing,
                    async_throughput=candidate_async_throughput,
                )
            )

    def run_and_parse_tests(
        self,
        testing_type: TestingMode,
        test_env: dict[str, str],
        test_files: TestFiles,
        optimization_iteration: int,
        testing_time: float = TOTAL_LOOPING_TIME_EFFECTIVE,
        *,
        enable_coverage: bool = False,
        pytest_min_loops: int = 5,
        pytest_max_loops: int = 100_000,
        code_context: CodeOptimizationContext | None = None,
        unittest_loop_index: int | None = None,
        line_profiler_output_file: Path | None = None,
    ) -> tuple[TestResults | dict, CoverageData | None]:
        coverage_database_file = None
        coverage_config_file = None
        try:
            if testing_type == TestingMode.BEHAVIOR:
                result_file_path, run_result, coverage_database_file, coverage_config_file = run_behavioral_tests(
                    test_files,
                    test_framework=self.test_cfg.test_framework,
                    cwd=self.project_root,
                    test_env=test_env,
                    pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
                    verbose=True,
                    enable_coverage=enable_coverage,
                )
            elif testing_type == TestingMode.LINE_PROFILE:
                result_file_path, run_result = run_line_profile_tests(
                    test_files,
                    cwd=self.project_root,
                    test_env=test_env,
                    pytest_cmd=self.test_cfg.pytest_cmd,
                    pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
                    pytest_target_runtime_seconds=testing_time,
                    pytest_min_loops=1,
                    pytest_max_loops=1,
                    test_framework=self.test_cfg.test_framework,
                    line_profiler_output_file=line_profiler_output_file,
                )
            elif testing_type == TestingMode.PERFORMANCE:
                result_file_path, run_result = run_benchmarking_tests(
                    test_files,
                    cwd=self.project_root,
                    test_env=test_env,
                    pytest_cmd=self.test_cfg.pytest_cmd,
                    pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
                    pytest_target_runtime_seconds=testing_time,
                    pytest_min_loops=pytest_min_loops,
                    pytest_max_loops=pytest_max_loops,
                    test_framework=self.test_cfg.test_framework,
                )
            else:
                msg = f"Unexpected testing type: {testing_type}"
                raise ValueError(msg)
        except subprocess.TimeoutExpired:
            logger.exception(
                f"Error running tests in {', '.join(str(f) for f in test_files.test_files)}.\nTimeout Error"
            )
            return TestResults(), None
        if run_result.returncode != 0 and testing_type == TestingMode.BEHAVIOR:
            logger.debug(
                f"!lsp|Nonzero return code {run_result.returncode} when running tests in "
                f"{', '.join([str(f.instrumented_behavior_file_path) for f in test_files.test_files])}.\n"
                f"stdout: {run_result.stdout}\n"
                f"stderr: {run_result.stderr}\n"
            )
            if "ModuleNotFoundError" in run_result.stdout:
                from rich.text import Text

                match = ImportErrorPattern.search(run_result.stdout).group()
                panel = Panel(Text.from_markup(f"⚠️  {match} ", style="bold red"), expand=False)
                console.print(panel)
        if testing_type in {TestingMode.BEHAVIOR, TestingMode.PERFORMANCE}:
            results, coverage_results = parse_test_results(
                test_xml_path=result_file_path,
                test_files=test_files,
                test_config=self.test_cfg,
                optimization_iteration=optimization_iteration,
                run_result=run_result,
                unittest_loop_index=unittest_loop_index,
                function_name=self.function_to_optimize.function_name,
                source_file=self.function_to_optimize.file_path,
                code_context=code_context,
                coverage_database_file=coverage_database_file,
                coverage_config_file=coverage_config_file,
            )
            if testing_type == TestingMode.PERFORMANCE:
                results.perf_stdout = run_result.stdout
            return results, coverage_results
        results, coverage_results = parse_line_profile_results(line_profiler_output_file=line_profiler_output_file)
        return results, coverage_results

    def submit_test_generation_tasks(
        self,
        executor: concurrent.futures.ThreadPoolExecutor,
        source_code_being_tested: str,
        helper_function_names: list[str],
        generated_test_paths: list[Path],
        generated_perf_test_paths: list[Path],
    ) -> list[concurrent.futures.Future]:
        return [
            executor.submit(
                generate_tests,
                self.aiservice_client,
                source_code_being_tested,
                self.function_to_optimize,
                helper_function_names,
                Path(self.original_module_path),
                self.test_cfg,
                INDIVIDUAL_TESTCASE_TIMEOUT,
                self.function_trace_id,
                test_index,
                test_path,
                test_perf_path,
            )
            for test_index, (test_path, test_perf_path) in enumerate(
                zip(generated_test_paths, generated_perf_test_paths)
            )
        ]

    def cleanup_generated_files(self) -> None:
        paths_to_cleanup = []
        for test_file in self.test_files:
            paths_to_cleanup.append(test_file.instrumented_behavior_file_path)
            paths_to_cleanup.append(test_file.benchmarking_file_path)

        cleanup_paths(paths_to_cleanup)

    def get_test_env(
        self, codeflash_loop_index: int, codeflash_test_iteration: int, codeflash_tracer_disable: int = 1
    ) -> dict:
        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = str(codeflash_test_iteration)
        test_env["CODEFLASH_TRACER_DISABLE"] = str(codeflash_tracer_disable)
        test_env["CODEFLASH_LOOP_INDEX"] = str(codeflash_loop_index)
        if "PYTHONPATH" not in test_env:
            test_env["PYTHONPATH"] = str(self.args.project_root)
        else:
            test_env["PYTHONPATH"] += os.pathsep + str(self.args.project_root)
        return test_env

    def line_profiler_step(
        self, code_context: CodeOptimizationContext, original_helper_code: dict[Path, str], candidate_index: int
    ) -> dict:
        try:
            console.rule()

            test_env = self.get_test_env(
                codeflash_loop_index=0, codeflash_test_iteration=candidate_index, codeflash_tracer_disable=1
            )
            line_profiler_output_file = add_decorator_imports(self.function_to_optimize, code_context)
            line_profile_results, _ = self.run_and_parse_tests(
                testing_type=TestingMode.LINE_PROFILE,
                test_env=test_env,
                test_files=self.test_files,
                optimization_iteration=0,
                testing_time=TOTAL_LOOPING_TIME_EFFECTIVE,
                enable_coverage=False,
                code_context=code_context,
                line_profiler_output_file=line_profiler_output_file,
            )
        finally:
            # Remove codeflash capture
            self.write_code_and_helpers(
                self.function_to_optimize_source_code, original_helper_code, self.function_to_optimize.file_path
            )
        if line_profile_results["str_out"] == "":
            logger.warning(
                f"Couldn't run line profiler for original function {self.function_to_optimize.function_name}"
            )
        return line_profile_results
