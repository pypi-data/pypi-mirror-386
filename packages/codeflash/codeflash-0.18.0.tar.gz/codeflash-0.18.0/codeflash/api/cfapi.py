from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import git
import requests
import sentry_sdk
from pydantic.json import pydantic_encoder

from codeflash.cli_cmds.console import console, logger
from codeflash.code_utils.env_utils import ensure_codeflash_api_key, get_codeflash_api_key, get_pr_number
from codeflash.code_utils.git_utils import get_current_branch, get_repo_owner_and_name
from codeflash.github.PrComment import FileDiffContent, PrComment
from codeflash.lsp.helpers import is_LSP_enabled
from codeflash.version import __version__

if TYPE_CHECKING:
    from requests import Response

    from codeflash.result.explanation import Explanation

from packaging import version

if os.environ.get("CODEFLASH_CFAPI_SERVER", "prod").lower() == "local":
    CFAPI_BASE_URL = "http://localhost:3001"
    CFWEBAPP_BASE_URL = "http://localhost:3000"
    logger.info(f"Using local CF API at {CFAPI_BASE_URL}.")
    console.rule()
else:
    CFAPI_BASE_URL = "https://app.codeflash.ai"
    CFWEBAPP_BASE_URL = "https://app.codeflash.ai"


def make_cfapi_request(
    endpoint: str,
    method: str,
    payload: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
    *,
    api_key: str | None = None,
    suppress_errors: bool = False,
) -> Response:
    """Make an HTTP request using the specified method, URL, headers, and JSON payload.

    :param endpoint: The endpoint URL to send the request to.
    :param method: The HTTP method to use ('GET', 'POST', etc.).
    :param payload: Optional JSON payload to include in the POST request body.
    :param suppress_errors: If True, suppress error logging for HTTP errors.
    :return: The response object from the API.
    """
    url = f"{CFAPI_BASE_URL}/cfapi{endpoint}"
    cfapi_headers = {"Authorization": f"Bearer {api_key or get_codeflash_api_key()}"}
    if extra_headers:
        cfapi_headers.update(extra_headers)
    try:
        if method.upper() == "POST":
            json_payload = json.dumps(payload, indent=None, default=pydantic_encoder)
            cfapi_headers["Content-Type"] = "application/json"
            response = requests.post(url, data=json_payload, headers=cfapi_headers, timeout=60)
        else:
            response = requests.get(url, headers=cfapi_headers, timeout=60)
        response.raise_for_status()
        return response  # noqa: TRY300
    except requests.exceptions.HTTPError:
        # response may be either a string or JSON, so we handle both cases
        error_message = ""
        try:
            json_response = response.json()
            if "error" in json_response:
                error_message = json_response["error"]
            elif "message" in json_response:
                error_message = json_response["message"]
        except (ValueError, TypeError):
            error_message = response.text

        if not suppress_errors:
            logger.error(
                f"CF_API_Error:: making request to Codeflash API (url: {url}, method: {method}, status {response.status_code}): {error_message}"
            )
        return response


@lru_cache(maxsize=1)
def get_user_id(api_key: Optional[str] = None) -> Optional[str]:
    """Retrieve the user's userid by making a request to the /cfapi/cli-get-user endpoint.

    :return: The userid or None if the request fails.
    """
    if not ensure_codeflash_api_key():
        return None

    response = make_cfapi_request(
        endpoint="/cli-get-user", method="GET", extra_headers={"cli_version": __version__}, api_key=api_key
    )
    if response.status_code == 200:
        if "min_version" not in response.text:
            return response.text
        resp_json = response.json()
        userid: str | None = resp_json.get("userId")
        min_version: str | None = resp_json.get("min_version")
        if userid:
            if min_version and version.parse(min_version) > version.parse(__version__):
                msg = "Your Codeflash CLI version is outdated. Please update to the latest version using `pip install --upgrade codeflash`."
                console.print(f"[bold red]{msg}[/bold red]")
                if is_LSP_enabled():
                    logger.debug(msg)
                    return f"Error: {msg}"
                sys.exit(1)
            return userid

        logger.error("Failed to retrieve userid from the response.")
        return None

    logger.error(f"Failed to look up your userid; is your CF API key valid? ({response.reason})")
    return None


def suggest_changes(
    owner: str,
    repo: str,
    pr_number: int,
    file_changes: dict[str, FileDiffContent],
    pr_comment: PrComment,
    existing_tests: str,
    generated_tests: str,
    trace_id: str,
    coverage_message: str,
    replay_tests: str = "",
    concolic_tests: str = "",
    optimization_review: str = "",
) -> Response:
    """Suggest changes to a pull request.

    Will make a review suggestion when possible;
    or create a new dependent pull request with the suggested changes.
    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param pr_number: The number of the pull request.
    :param file_changes: A dictionary of file changes.
    :param pr_comment: The pull request comment object, containing the optimization explanation, best runtime, etc.
    :param generated_tests: The generated tests.
    :return: The response object.
    """
    payload = {
        "owner": owner,
        "repo": repo,
        "pullNumber": pr_number,
        "diffContents": file_changes,
        "prCommentFields": pr_comment.to_json(),
        "existingTests": existing_tests,
        "generatedTests": generated_tests,
        "traceId": trace_id,
        "coverage_message": coverage_message,
        "replayTests": replay_tests,
        "concolicTests": concolic_tests,
        "optimizationImpact": optimization_review,  # impact keyword left for legacy reasons, touches js/ts code
    }
    return make_cfapi_request(endpoint="/suggest-pr-changes", method="POST", payload=payload)


def create_pr(
    owner: str,
    repo: str,
    base_branch: str,
    file_changes: dict[str, FileDiffContent],
    pr_comment: PrComment,
    existing_tests: str,
    generated_tests: str,
    trace_id: str,
    coverage_message: str,
    replay_tests: str = "",
    concolic_tests: str = "",
    optimization_review: str = "",
) -> Response:
    """Create a pull request, targeting the specified branch. (usually 'main').

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param base_branch: The base branch to target.
    :param file_changes: A dictionary of file changes.
    :param pr_comment: The pull request comment object, containing the optimization explanation, best runtime, etc.
    :param generated_tests: The generated tests.
    :return: The response object.
    """
    # convert Path objects to strings
    payload = {
        "owner": owner,
        "repo": repo,
        "baseBranch": base_branch,
        "diffContents": file_changes,
        "prCommentFields": pr_comment.to_json(),
        "existingTests": existing_tests,
        "generatedTests": generated_tests,
        "traceId": trace_id,
        "coverage_message": coverage_message,
        "replayTests": replay_tests,
        "concolicTests": concolic_tests,
        "optimizationImpact": optimization_review,  # Impact keyword left for legacy reasons, it touches js/ts codebase
    }
    return make_cfapi_request(endpoint="/create-pr", method="POST", payload=payload)


def create_staging(
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
    optimization_review: str = "",
) -> Response:
    """Create a staging pull request, targeting the specified branch. (usually 'staging').

    :param original_code: A mapping of file paths to original source code.
    :param new_code: A mapping of file paths to optimized source code.
    :param explanation: An Explanation object with optimization details.
    :param existing_tests_source: Existing test code.
    :param generated_original_test_source: Generated tests for the original function.
    :param function_trace_id: Unique identifier for this optimization trace.
    :param coverage_message: Coverage report or summary.
    :return: The response object from the backend.
    """
    relative_path = explanation.file_path.relative_to(root_dir).as_posix()

    build_file_changes = {
        Path(p).relative_to(root_dir).as_posix(): FileDiffContent(oldContent=original_code[p], newContent=new_code[p])
        for p in original_code
    }

    payload = {
        "baseBranch": get_current_branch(),
        "diffContents": build_file_changes,
        "prCommentFields": PrComment(
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
        ).to_json(),
        "existingTests": existing_tests_source,
        "generatedTests": generated_original_test_source,
        "traceId": function_trace_id,
        "coverage_message": coverage_message,
        "replayTests": replay_tests,
        "concolicTests": concolic_tests,
        "optimizationImpact": optimization_review,  # Impact keyword left for legacy reasons, it touches js/ts codebase
    }

    return make_cfapi_request(endpoint="/create-staging", method="POST", payload=payload)


def is_github_app_installed_on_repo(owner: str, repo: str, *, suppress_errors: bool = False) -> bool:
    """Check if the Codeflash GitHub App is installed on the specified repository.

    :param owner: The owner of the repository.
    :param repo: The name of the repository.
    :param suppress_errors: If True, suppress error logging when the app is not installed.
    :return: True if the app is installed, False otherwise.
    """
    response = make_cfapi_request(
        endpoint=f"/is-github-app-installed?repo={repo}&owner={owner}", method="GET", suppress_errors=suppress_errors
    )
    return response.ok and response.text == "true"


def get_blocklisted_functions() -> dict[str, set[str]] | dict[str, Any]:
    """Retrieve blocklisted functions for the current pull request.

    Returns A dictionary mapping filenames to sets of blocklisted function names.
    """
    pr_number = get_pr_number()
    if pr_number is None:
        return {}

    try:
        owner, repo = get_repo_owner_and_name()
        information = {"pr_number": pr_number, "repo_owner": owner, "repo_name": repo}

        req = make_cfapi_request(endpoint="/verify-existing-optimizations", method="POST", payload=information)
        req.raise_for_status()
        content: dict[str, list[str]] = req.json()
    except Exception as e:
        logger.error(f"Error getting blocklisted functions: {e}")
        sentry_sdk.capture_exception(e)
        return {}

    return {Path(k).name: {v.replace("()", "") for v in values} for k, values in content.items()}


def is_function_being_optimized_again(
    owner: str, repo: str, pr_number: int, code_contexts: list[dict[str, str]]
) -> Any:  # noqa: ANN401
    """Check if the function being optimized is being optimized again."""
    response = make_cfapi_request(
        "/is-already-optimized",
        "POST",
        {"owner": owner, "repo": repo, "pr_number": pr_number, "code_contexts": code_contexts},
    )
    response.raise_for_status()
    return response.json()


def add_code_context_hash(code_context_hash: str) -> None:
    """Add code context to the DB cache."""
    pr_number = get_pr_number()
    if pr_number is None:
        return
    try:
        owner, repo = get_repo_owner_and_name()
        pr_number = get_pr_number()
    except git.exc.InvalidGitRepositoryError:
        return

    if owner and repo and pr_number is not None:
        make_cfapi_request(
            "/add-code-hash",
            "POST",
            {"owner": owner, "repo": repo, "pr_number": pr_number, "code_hash": code_context_hash},
        )


def mark_optimization_success(trace_id: str, *, is_optimization_found: bool) -> Response:
    """Mark an optimization event as success or not.

    :param trace_id: The unique identifier for the optimization event.
    :param is_optimization_found: Boolean indicating whether the optimization was found.
    :return: The response object from the API.
    """
    payload = {"trace_id": trace_id, "is_optimization_found": is_optimization_found}
    return make_cfapi_request(endpoint="/mark-as-success", method="POST", payload=payload)


def send_completion_email() -> Response:
    """Send an email notification when codeflash --all completes."""
    try:
        owner, repo = get_repo_owner_and_name()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        response = requests.Response()
        response.status_code = 500
        return response
    payload = {"owner": owner, "repo": repo}
    return make_cfapi_request(endpoint="/send-completion-email", method="POST", payload=payload)
