from __future__ import annotations

import asyncio
import concurrent.futures
import time
import threading
from typing import List, Tuple, TYPE_CHECKING
from rich import print as rprint

from judgeval.data import ScorerData, ScoringResult
from judgeval.scorers.score import a_execute_scoring
from judgeval.api import JudgmentSyncClient
from judgeval.env import (
    JUDGMENT_MAX_CONCURRENT_EVALUATIONS,
)
from judgeval.exceptions import JudgmentAPIError, JudgmentRuntimeError
from judgeval.logger import judgeval_logger

from judgeval.env import JUDGMENT_API_KEY, JUDGMENT_ORG_ID

if TYPE_CHECKING:
    from judgeval.data.evaluation_run import ExampleEvaluationRun


def safe_run_async(coro):
    """
    Safely run an async coroutine whether or not there's already an event loop running.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the running loop
        asyncio.get_running_loop()
        # If we get here, there's already a loop running
        # Run in a separate thread to avoid "asyncio.run() cannot be called from a running event loop"
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No event loop is running, safe to use asyncio.run()
        return asyncio.run(coro)


def log_evaluation_results(
    scoring_results: List[ScoringResult],
    run: ExampleEvaluationRun,
) -> str:
    """
    Logs evaluation results to the Judgment API database.

    Args:
        merged_results (List[ScoringResult]): The results to log
        evaluation_run (EvaluationRun): The evaluation run containing project info and API key
        judgment_api_key (str): The API key for the Judgment API

    Raises:
        JudgmentAPIError: If there's an API error during logging
        ValueError: If there's a validation error with the results
    """
    try:
        if not JUDGMENT_API_KEY or not JUDGMENT_ORG_ID:
            raise ValueError("API key and organization ID are required")

        api_client = JudgmentSyncClient(JUDGMENT_API_KEY, JUDGMENT_ORG_ID)
        response = api_client.log_eval_results(
            {
                "results": scoring_results,  # type: ignore
                "run": run.model_dump(warnings=False),  # type: ignore
            }
        )
        url = response.get("ui_results_url")
        return url

    except Exception as e:
        judgeval_logger.error(f"Failed to save evaluation results to DB: {str(e)}")
        raise JudgmentRuntimeError(
            f"Request failed while saving evaluation results to DB: {str(e)}"
        )


def _poll_evaluation_until_complete(
    evaluation_run: ExampleEvaluationRun,
    expected_examples_count: int,
    poll_interval_seconds: float = 5,
    max_failures: int = 5,
    max_poll_count: int = 60,  # This should be equivalent to 5 minutes
) -> Tuple[List[ScoringResult], str]:
    """
    Polls until the evaluation is complete and returns the results.

    Args:
        eval_name (str): Name of the evaluation run
        project_name (str): Name of the project
        judgment_api_key (str): API key for authentication
        organization_id (str): Organization ID for the evaluation
        poll_interval_seconds (int, optional): Time between status checks in seconds. Defaults to 5.
        original_examples (List[Example], optional): The original examples sent for evaluation.
                                                    If provided, will match results with original examples.

    Returns:
        List[ScoringResult]: The evaluation results
    """
    project_name = evaluation_run.project_name
    experiment_run_id = evaluation_run.id

    if not project_name or not experiment_run_id:
        raise ValueError("Project name and experiment run ID are required")

    poll_count = 0
    exception_count = 0
    api_client = JudgmentSyncClient(JUDGMENT_API_KEY, JUDGMENT_ORG_ID)
    while poll_count < max_poll_count:
        poll_count += 1
        try:
            # Check status
            results_response = api_client.fetch_experiment_run(
                {
                    "experiment_run_id": experiment_run_id,
                    "project_name": project_name,
                }
            )

            example_scorer_pairings = results_response.get("results", [])
            if len(example_scorer_pairings) != expected_examples_count:
                time.sleep(poll_interval_seconds)
                continue

            url = results_response.get("ui_results_url")

            scoring_result_list = []
            for res in example_scorer_pairings:
                example = res.get("data", {}).copy()
                example["example_id"] = res.get("example_id")
                scoring_result = ScoringResult(
                    scorers_data=res.get("scorers", []),
                    success=all(
                        t.get("success", False) for t in res.get("scorers", [])
                    ),
                    data_object=example,
                )
                scoring_result_list.append(scoring_result)

            return scoring_result_list, url
        except Exception as e:
            exception_count += 1
            if isinstance(e, JudgmentAPIError):
                raise

            judgeval_logger.error(f"Error checking evaluation status: {str(e)}")
            if exception_count > max_failures:
                raise JudgmentRuntimeError(
                    f"Error checking evaluation status after {poll_count} attempts: {str(e)}"
                )

            time.sleep(poll_interval_seconds)

    raise JudgmentRuntimeError(
        f"Error checking evaluation status after {poll_count} attempts"
    )


def progress_logger(stop_event, msg="Working...", interval=5):
    start = time.time()
    while not stop_event.is_set():
        elapsed = int(time.time() - start)
        judgeval_logger.info(f"{msg} ({elapsed} sec)")
        stop_event.wait(interval)


def run_eval(
    evaluation_run: ExampleEvaluationRun,
) -> List[ScoringResult]:
    """
    Executes an evaluation of `Example`s using one or more `Scorer`s

    Args:
        evaluation_run (ExampleEvaluationRun): Stores example and evaluation together for running

    Returns:
        List[ScoringResult]: A list of ScoringResult objects
    """
    # Check that every example has the same keys
    keys = evaluation_run.examples[0].get_fields().keys()
    for example in evaluation_run.examples:
        current_keys = example.get_fields().keys()
        if current_keys != keys:
            raise ValueError(
                f"All examples must have the same keys: {current_keys} != {keys}"
            )

    results: List[ScoringResult] = []
    url = ""

    if (
        len(evaluation_run.custom_scorers) > 0
        and len(evaluation_run.judgment_scorers) > 0
    ):
        error_msg = "We currently do not support running both local and Judgment API scorers at the same time. Please run your evaluation with either local scorers or Judgment API scorers, but not both."
        judgeval_logger.error(error_msg)
        raise ValueError(error_msg)

    e2b_scorers = [cs for cs in evaluation_run.custom_scorers if cs.server_hosted]

    if evaluation_run.judgment_scorers or e2b_scorers:
        if evaluation_run.judgment_scorers and e2b_scorers:
            error_msg = "We currently do not support running both hosted custom scorers and Judgment API scorers at the same time. Please run your evaluation with one or the other, but not both."
            judgeval_logger.error(error_msg)
            raise ValueError(error_msg)

        if len(e2b_scorers) > 1:
            error_msg = "We currently do not support running multiple hosted custom scorers at the same time."
            judgeval_logger.error(error_msg)
            raise ValueError(error_msg)

        stop_event = threading.Event()
        t = threading.Thread(
            target=progress_logger, args=(stop_event, "Running evaluation...")
        )
        t.start()
        try:
            api_client = JudgmentSyncClient(JUDGMENT_API_KEY, JUDGMENT_ORG_ID)
            response = api_client.add_to_run_eval_queue_examples(
                evaluation_run.model_dump(warnings=False)  # type: ignore
            )

            if not response.get("success", False):
                error_message = response.error
                judgeval_logger.error(
                    f"Error adding evaluation to queue: {error_message}"
                )
                raise JudgmentRuntimeError(error_message)

            results, url = _poll_evaluation_until_complete(
                evaluation_run=evaluation_run,
                expected_examples_count=len(evaluation_run.examples),
            )
        finally:
            stop_event.set()
            t.join()
    else:
        results = safe_run_async(
            a_execute_scoring(
                evaluation_run.examples,
                evaluation_run.custom_scorers,
                model=evaluation_run.model,
                throttle_value=0,
                max_concurrent=JUDGMENT_MAX_CONCURRENT_EVALUATIONS,
            )
        )

        send_results = [
            scoring_result.model_dump(warnings=False) for scoring_result in results
        ]
        url = log_evaluation_results(send_results, evaluation_run)
    rprint(
        f"\n🔍 You can view your evaluation results here: [rgb(106,0,255)][link={url}]View Results[/link]\n"
    )
    return results


def assert_test(scoring_results: List[ScoringResult]) -> None:
    """
    Collects all failed scorers from the scoring results.

    Args:
        ScoringResults (List[ScoringResult]): List of scoring results to check

    Returns:
        None. Raises exceptions for any failed test cases.
    """
    failed_cases: List[List[ScorerData]] = []

    for result in scoring_results:
        if not result.success:
            # Create a test case context with all relevant fields
            test_case: List[ScorerData] = []
            if result.scorers_data:
                # If the result was not successful, check each scorer_data
                for scorer_data in result.scorers_data:
                    if not scorer_data.success:
                        test_case.append(scorer_data)
            failed_cases.append(test_case)

    if failed_cases:
        error_msg = "The following test cases failed: \n"
        for fail_case in failed_cases:
            for fail_scorer in fail_case:
                error_msg += (
                    f"\nScorer Name: {fail_scorer.name}\n"
                    f"Threshold: {fail_scorer.threshold}\n"
                    f"Success: {fail_scorer.success}\n"
                    f"Score: {fail_scorer.score}\n"
                    f"Reason: {fail_scorer.reason}\n"
                    f"Strict Mode: {fail_scorer.strict_mode}\n"
                    f"Evaluation Model: {fail_scorer.evaluation_model}\n"
                    f"Error: {fail_scorer.error}\n"
                    f"Additional Metadata: {fail_scorer.additional_metadata}\n"
                )
            error_msg += "-" * 100

        total_tests = len(scoring_results)
        failed_tests = len(failed_cases)
        passed_tests = total_tests - failed_tests

        # Print summary with colors
        rprint("\n" + "=" * 80)
        if failed_tests == 0:
            rprint(
                f"[bold green]🎉 ALL TESTS PASSED! {passed_tests}/{total_tests} tests successful[/bold green]"
            )
        else:
            rprint(
                f"[bold red]⚠️  TEST RESULTS: {passed_tests}/{total_tests} passed ({failed_tests} failed)[/bold red]"
            )
        rprint("=" * 80 + "\n")

        # Print individual test cases
        for i, result in enumerate(scoring_results):
            test_num = i + 1
            if result.success:
                rprint(f"[green]✓ Test {test_num}: PASSED[/green]")
            else:
                rprint(f"[red]✗ Test {test_num}: FAILED[/red]")
                if result.scorers_data:
                    for scorer_data in result.scorers_data:
                        if not scorer_data.success:
                            rprint(f"  [yellow]Scorer: {scorer_data.name}[/yellow]")
                            rprint(f"  [red]  Score: {scorer_data.score}[/red]")
                            rprint(f"  [red]  Reason: {scorer_data.reason}[/red]")
                            if scorer_data.error:
                                rprint(f"  [red]  Error: {scorer_data.error}[/red]")
                rprint("  " + "-" * 40)

        rprint("\n" + "=" * 80)
        if failed_tests > 0:
            raise AssertionError(failed_cases)
