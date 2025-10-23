import asyncio
import logging

import rich_click as click

from ..actions import ProcessJobsAction
from ..channels import Channel
from ..utils import async_to_sync

__all__ = ["run_job_server"]

logger = logging.getLogger(__name__)


async def _run_job_server(
    channel: Channel,
    num_test_entries: int,
    ratio_valid_entries: float,
    maximum_depth: int,
    # reading options for readers
    max_num_lines_mol_block: int,
    data_dir: str,
) -> None:
    await channel.start()

    action = ProcessJobsAction(
        channel,
        num_test_entries,
        ratio_valid_entries,
        maximum_depth,
        max_num_lines_mol_block,
        data_dir,
    )

    task = asyncio.create_task(action.run())
    try:
        logging.info(f"Running action {action}")
        await task
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        task.cancel()
        await task

        await channel.stop()


@click.command(context_settings={"show_default": True})
@click.option(
    "--channel",
    type=click.Choice(["kafka"], case_sensitive=False),
    default="kafka",
    help="Channel to use for communication with the model.",
)
@click.option(
    "--broker-url",
    default="localhost:9092",
    help="Broker url to connect to.",
)
@click.option(
    "--num-test-entries",
    default=10,
    help="Number of entries to use for guessing the format of the input file.",
)
@click.option(
    "--ratio-valid-entries",
    default=0.6,
    help="Ratio of valid entries to use for guessing the format of the input file.",
)
@click.option(
    "--maximum-depth",
    default=50,
    help="Maximum level of nesting allowed for reading files.",
)
@click.option(
    "--max-num-lines-mol-block",
    default=10_000,
    help="Maximum number of lines in a molecule block before giving up parsing.",
)
@click.option(
    "--data-dir",
    default="sources",
    help="Directory containing structure files associated with the incoming jobs.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error", "critical"], case_sensitive=False),
    help="The logging level.",
)
@async_to_sync
async def run_job_server(
    # communication options
    channel: str,
    broker_url: str,
    # reading options for DepthFirstExplorer
    num_test_entries: int,
    ratio_valid_entries: float,
    maximum_depth: int,
    # reading options for readers
    max_num_lines_mol_block: int,
    data_dir: str,
    # log level
    log_level: str,
) -> None:
    logging.basicConfig(level=log_level.upper())

    channel_instance = Channel.create_channel(channel, broker_url=broker_url)

    await _run_job_server(
        channel=channel_instance,
        num_test_entries=num_test_entries,
        ratio_valid_entries=ratio_valid_entries,
        maximum_depth=maximum_depth,
        max_num_lines_mol_block=max_num_lines_mol_block,
        data_dir=data_dir,
    )
