from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import git

from codeflash.api import cfapi
from codeflash.cli_cmds.console import console, logger
from codeflash.code_utils import env_utils
from codeflash.code_utils.code_replacer import is_zero_diff
from codeflash.code_utils.git_utils import check_and_push_branch, get_current_branch, get_repo_owner_and_name
from codeflash.code_utils.github_utils import github_pr_url
from codeflash.code_utils.tabulate import tabulate
from codeflash.code_utils.time_utils import format_perf, format_time
from codeflash.github.PrComment import FileDiffContent, PrComment
from codeflash.result.critic import performance_gain

if TYPE_CHECKING:
    from codeflash.models.models import FunctionCalledInTest, InvocationId
    from codeflash.result.explanation import Explanation
    from codeflash.verification.verification_utils import TestConfig


def existing_tests_source_for(
    function_qualified_name_with_modules_from_root: str,
    function_to_tests: dict[str, set[FunctionCalledInTest]],
    test_cfg: TestConfig,
    original_runtimes_all: dict[InvocationId, list[int]],
    optimized_runtimes_all: dict[InvocationId, list[int]],
) -> tuple[str, str, str]:
    test_files = function_to_tests.get(function_qualified_name_with_modules_from_root)
    if not test_files:
        return "", "", ""
    output_existing: str = ""
    output_concolic: str = ""
    output_replay: str = ""
    rows_existing = []
    rows_concolic = []
    rows_replay = []
    headers = ["Test File::Test Function", "Original ⏱️", "Optimized ⏱️", "Speedup"]
    tests_root = test_cfg.tests_root
    original_tests_to_runtimes: dict[Path, dict[str, int]] = {}
    optimized_tests_to_runtimes: dict[Path, dict[str, int]] = {}
    non_generated_tests = set()
    for test_file in test_files:
        non_generated_tests.add(test_file.tests_in_file.test_file)
    # TODO confirm that original and optimized have the same keys
    all_invocation_ids = original_runtimes_all.keys() | optimized_runtimes_all.keys()
    for invocation_id in all_invocation_ids:
        abs_path = Path(invocation_id.test_module_path.replace(".", os.sep)).with_suffix(".py").resolve()
        if abs_path not in non_generated_tests:
            continue
        if abs_path not in original_tests_to_runtimes:
            original_tests_to_runtimes[abs_path] = {}
        if abs_path not in optimized_tests_to_runtimes:
            optimized_tests_to_runtimes[abs_path] = {}
        qualified_name = (
            invocation_id.test_class_name + "." + invocation_id.test_function_name  # type: ignore[operator]
            if invocation_id.test_class_name
            else invocation_id.test_function_name
        )
        if qualified_name not in original_tests_to_runtimes[abs_path]:
            original_tests_to_runtimes[abs_path][qualified_name] = 0  # type: ignore[index]
        if qualified_name not in optimized_tests_to_runtimes[abs_path]:
            optimized_tests_to_runtimes[abs_path][qualified_name] = 0  # type: ignore[index]
        if invocation_id in original_runtimes_all:
            original_tests_to_runtimes[abs_path][qualified_name] += min(original_runtimes_all[invocation_id])  # type: ignore[index]
        if invocation_id in optimized_runtimes_all:
            optimized_tests_to_runtimes[abs_path][qualified_name] += min(optimized_runtimes_all[invocation_id])  # type: ignore[index]
    # parse into string
    all_abs_paths = (
        original_tests_to_runtimes.keys()
    )  # both will have the same keys as some default values are assigned in the previous loop
    for filename in sorted(all_abs_paths):
        all_qualified_names = original_tests_to_runtimes[
            filename
        ].keys()  # both will have the same keys as some default values are assigned in the previous loop
        for qualified_name in sorted(all_qualified_names):
            # if not present in optimized output nan
            if (
                original_tests_to_runtimes[filename][qualified_name] != 0
                and optimized_tests_to_runtimes[filename][qualified_name] != 0
            ):
                print_optimized_runtime = format_time(optimized_tests_to_runtimes[filename][qualified_name])
                print_original_runtime = format_time(original_tests_to_runtimes[filename][qualified_name])
                print_filename = filename.resolve().relative_to(tests_root.resolve()).as_posix()
                greater = (
                    optimized_tests_to_runtimes[filename][qualified_name]
                    > original_tests_to_runtimes[filename][qualified_name]
                )
                perf_gain = format_perf(
                    performance_gain(
                        original_runtime_ns=original_tests_to_runtimes[filename][qualified_name],
                        optimized_runtime_ns=optimized_tests_to_runtimes[filename][qualified_name],
                    )
                    * 100
                )
                if greater:
                    if "__replay_test_" in str(print_filename):
                        rows_replay.append(
                            [
                                f"`{print_filename}::{qualified_name}`",
                                f"{print_original_runtime}",
                                f"{print_optimized_runtime}",
                                f"{perf_gain}%⚠️",
                            ]
                        )
                    elif "codeflash_concolic" in str(print_filename):
                        rows_concolic.append(
                            [
                                f"`{print_filename}::{qualified_name}`",
                                f"{print_original_runtime}",
                                f"{print_optimized_runtime}",
                                f"{perf_gain}%⚠️",
                            ]
                        )
                    else:
                        rows_existing.append(
                            [
                                f"`{print_filename}::{qualified_name}`",
                                f"{print_original_runtime}",
                                f"{print_optimized_runtime}",
                                f"{perf_gain}%⚠️",
                            ]
                        )
                elif "__replay_test_" in str(print_filename):
                    rows_replay.append(
                        [
                            f"`{print_filename}::{qualified_name}`",
                            f"{print_original_runtime}",
                            f"{print_optimized_runtime}",
                            f"{perf_gain}%✅",
                        ]
                    )
                elif "codeflash_concolic" in str(print_filename):
                    rows_concolic.append(
                        [
                            f"`{print_filename}::{qualified_name}`",
                            f"{print_original_runtime}",
                            f"{print_optimized_runtime}",
                            f"{perf_gain}%✅",
                        ]
                    )
                else:
                    rows_existing.append(
                        [
                            f"`{print_filename}::{qualified_name}`",
                            f"{print_original_runtime}",
                            f"{print_optimized_runtime}",
                            f"{perf_gain}%✅",
                        ]
                    )
    output_existing += tabulate(  # type: ignore[no-untyped-call]
        headers=headers, tabular_data=rows_existing, tablefmt="pipe", colglobalalign=None, preserve_whitespace=True
    )
    output_existing += "\n"
    if len(rows_existing) == 0:
        output_existing = ""
    output_concolic += tabulate(  # type: ignore[no-untyped-call]
        headers=headers, tabular_data=rows_concolic, tablefmt="pipe", colglobalalign=None, preserve_whitespace=True
    )
    output_concolic += "\n"
    if len(rows_concolic) == 0:
        output_concolic = ""
    output_replay += tabulate(  # type: ignore[no-untyped-call]
        headers=headers, tabular_data=rows_replay, tablefmt="pipe", colglobalalign=None, preserve_whitespace=True
    )
    output_replay += "\n"
    if len(rows_replay) == 0:
        output_replay = ""
    return output_existing, output_replay, output_concolic


def check_create_pr(
    original_code: dict[Path, str],
    new_code: dict[Path, str],
    explanation: Explanation,
    existing_tests_source: str,
    generated_original_test_source: str,
    function_trace_id: str,
    coverage_message: str,
    replay_tests: str,
    concolic_tests: str,
    root_dir: Path,
    git_remote: Optional[str] = None,
    optimization_review: str = "",
) -> None:
    pr_number: Optional[int] = env_utils.get_pr_number()
    git_repo = git.Repo(search_parent_directories=True)

    if pr_number is not None:
        logger.info(f"Suggesting changes to PR #{pr_number} ...")
        owner, repo = get_repo_owner_and_name(git_repo)
        relative_path = explanation.file_path.resolve().relative_to(root_dir.resolve()).as_posix()
        build_file_changes = {
            Path(p).resolve().relative_to(root_dir.resolve()).as_posix(): FileDiffContent(
                oldContent=original_code[p], newContent=new_code[p]
            )
            for p in original_code
            if not is_zero_diff(original_code[p], new_code[p])
        }
        if not build_file_changes:
            logger.info("No changes to suggest to PR.")
            return
        response = cfapi.suggest_changes(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            file_changes=build_file_changes,
            pr_comment=PrComment(
                optimization_explanation=explanation.explanation_message(),
                best_runtime=explanation.best_runtime_ns,
                original_runtime=explanation.original_runtime_ns,
                function_name=explanation.function_name,
                relative_file_path=relative_path,
                speedup_x=explanation.speedup_x,
                speedup_pct=explanation.speedup_pct,
                winning_behavior_test_results=explanation.winning_behavior_test_results,
                winning_benchmarking_test_results=explanation.winning_benchmarking_test_results,
                benchmark_details=explanation.benchmark_details,
            ),
            existing_tests=existing_tests_source,
            generated_tests=generated_original_test_source,
            trace_id=function_trace_id,
            coverage_message=coverage_message,
            replay_tests=replay_tests,
            concolic_tests=concolic_tests,
            optimization_review=optimization_review,
        )
        if response.ok:
            logger.info(f"Suggestions were successfully made to PR #{pr_number}")
        else:
            logger.error(
                f"Optimization was successful, but I failed to suggest changes to PR #{pr_number}."
                f" Response from server was: {response.text}"
            )
    else:
        logger.info("Creating a new PR with the optimized code...")
        console.rule()
        owner, repo = get_repo_owner_and_name(git_repo, git_remote)
        logger.info(f"Pushing to {git_remote} - Owner: {owner}, Repo: {repo}")
        console.rule()
        if not check_and_push_branch(git_repo, git_remote, wait_for_push=True):
            logger.warning("⏭️ Branch is not pushed, skipping PR creation...")
            return
        relative_path = explanation.file_path.resolve().relative_to(root_dir.resolve()).as_posix()
        base_branch = get_current_branch()
        build_file_changes = {
            Path(p).resolve().relative_to(root_dir.resolve()).as_posix(): FileDiffContent(
                oldContent=original_code[p], newContent=new_code[p]
            )
            for p in original_code
        }

        response = cfapi.create_pr(
            owner=owner,
            repo=repo,
            base_branch=base_branch,
            file_changes=build_file_changes,
            pr_comment=PrComment(
                optimization_explanation=explanation.explanation_message(),
                best_runtime=explanation.best_runtime_ns,
                original_runtime=explanation.original_runtime_ns,
                function_name=explanation.function_name,
                relative_file_path=relative_path,
                speedup_x=explanation.speedup_x,
                speedup_pct=explanation.speedup_pct,
                winning_behavior_test_results=explanation.winning_behavior_test_results,
                winning_benchmarking_test_results=explanation.winning_benchmarking_test_results,
                benchmark_details=explanation.benchmark_details,
            ),
            existing_tests=existing_tests_source,
            generated_tests=generated_original_test_source,
            trace_id=function_trace_id,
            coverage_message=coverage_message,
            replay_tests=replay_tests,
            concolic_tests=concolic_tests,
            optimization_review=optimization_review,
        )
        if response.ok:
            pr_id = response.text
            pr_url = github_pr_url(owner, repo, pr_id)
            logger.info(f"Successfully created a new PR #{pr_id} with the optimized code: {pr_url}")
        else:
            logger.error(
                f"Optimization was successful, but I failed to create a PR with the optimized code."
                f" Response from server was: {response.text}"
            )
        console.rule()
