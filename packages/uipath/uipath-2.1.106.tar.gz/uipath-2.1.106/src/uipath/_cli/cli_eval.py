import ast
import asyncio
import os
from typing import List, Optional

import click

from uipath._cli._evals._console_progress_reporter import ConsoleProgressReporter
from uipath._cli._evals._evaluate import evaluate
from uipath._cli._evals._progress_reporter import StudioWebProgressReporter
from uipath._cli._evals._runtime import (
    UiPathEvalContext,
)
from uipath._cli._runtime._runtime_factory import generate_runtime_factory
from uipath._cli._utils._constants import UIPATH_PROJECT_ID
from uipath._cli._utils._folders import get_personal_workspace_key_async
from uipath._cli.middlewares import Middlewares
from uipath._events._event_bus import EventBus
from uipath.eval._helpers import auto_discover_entrypoint
from uipath.tracing import LlmOpsHttpExporter

from .._utils.constants import ENV_JOB_ID
from ..telemetry import track
from ._utils._console import ConsoleLogger
from ._utils._eval_set import EvalHelpers

console = ConsoleLogger()


class LiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except Exception as e:
            raise click.BadParameter(value) from e


def setup_reporting_prereq(no_report: bool) -> bool:
    if no_report:
        return False

    if not os.getenv(UIPATH_PROJECT_ID, False):
        console.warning(
            "UIPATH_PROJECT_ID environment variable not set. Results will no be reported to Studio Web."
        )
        return False
    if not os.getenv("UIPATH_FOLDER_KEY"):
        folder_key = asyncio.run(get_personal_workspace_key_async())
        if folder_key:
            os.environ["UIPATH_FOLDER_KEY"] = folder_key
    return True


@click.command()
@click.argument("entrypoint", required=False)
@click.argument("eval_set", required=False)
@click.option("--eval-ids", cls=LiteralOption, default="[]")
@click.option(
    "--no-report",
    is_flag=True,
    help="Do not report the evaluation results",
    default=False,
)
@click.option(
    "--workers",
    type=int,
    default=1,
    help="Number of parallel workers for running evaluations (default: 1)",
)
@click.option(
    "--output-file",
    required=False,
    type=click.Path(exists=False),
    help="File path where the output will be written",
)
@track(when=lambda *_a, **_kw: os.getenv(ENV_JOB_ID) is None)
def eval(
    entrypoint: Optional[str],
    eval_set: Optional[str],
    eval_ids: List[str],
    no_report: bool,
    workers: int,
    output_file: Optional[str],
) -> None:
    """Run an evaluation set against the agent.

    Args:
        entrypoint: Path to the agent script to evaluate (optional, will auto-discover if not specified)
        eval_set: Path to the evaluation set JSON file (optional, will auto-discover if not specified)
        eval_ids: Optional list of evaluation IDs
        workers: Number of parallel workers for running evaluations
        no_report: Do not report the evaluation results
    """
    context_args = {
        "entrypoint": entrypoint or auto_discover_entrypoint(),
        "eval_set": eval_set,
        "eval_ids": eval_ids,
        "workers": workers,
        "no_report": no_report,
        "output_file": output_file,
    }

    should_register_progress_reporter = setup_reporting_prereq(no_report)

    result = Middlewares.next(
        "eval",
        entrypoint,
        eval_set,
        eval_ids,
        no_report=no_report,
        workers=workers,
        execution_output_file=output_file,
        register_progress_reporter=should_register_progress_reporter,
    )

    if result.error_message:
        console.error(result.error_message)

    if result.should_continue:
        event_bus = EventBus()

        if should_register_progress_reporter:
            progress_reporter = StudioWebProgressReporter(LlmOpsHttpExporter())
            asyncio.run(progress_reporter.subscribe_to_eval_runtime_events(event_bus))

        eval_context = UiPathEvalContext.with_defaults(
            execution_output_file=output_file,
            entrypoint=context_args["entrypoint"],
        )

        eval_context.no_report = no_report
        eval_context.workers = workers
        eval_context.eval_set = eval_set or EvalHelpers.auto_discover_eval_set()
        eval_context.eval_ids = eval_ids

        console_reporter = ConsoleProgressReporter()
        asyncio.run(console_reporter.subscribe_to_eval_runtime_events(event_bus))

        try:
            runtime_factory = generate_runtime_factory()
            if eval_context.job_id:
                runtime_factory.add_span_exporter(LlmOpsHttpExporter())
            asyncio.run(evaluate(runtime_factory, eval_context, event_bus))

        except Exception as e:
            console.error(
                f"Error occurred: {e or 'Execution failed'}", include_traceback=True
            )


if __name__ == "__main__":
    eval()
