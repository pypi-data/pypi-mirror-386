import json
import logging
import os
from asyncio import get_running_loop, to_thread

from nerdd_module import WriteOutputStep

from ..channels import Channel
from ..files import FileSystem
from ..steps import PostprocessFromConfigStep, ReadPickleStep
from ..types import SerializationRequestMessage, SerializationResultMessage, Tombstone
from ..utils import run_pipeline
from .action import Action

__all__ = ["SerializeJobAction"]


logger = logging.getLogger(__name__)


class SerializeJobAction(Action[SerializationRequestMessage]):
    def __init__(self, channel: Channel, data_dir: str) -> None:
        super().__init__(channel.serialization_requests_topic())
        self._file_system = FileSystem(data_dir)

    async def _process_message(self, message: SerializationRequestMessage) -> None:
        job_id = message.job_id
        job_type = message.job_type
        params = message.params
        output_format = message.output_format
        logger.info(f"Write output for job {job_id} in format {output_format}")

        # check input files
        input_files = list(self._file_system.iter_results_file_paths(job_id))
        if len(input_files) == 0:
            logger.warning(f"No input files found for job {job_id}. Cannot serialize.")
            return

        # remove specific parameter keys that could induce vulnerabilities
        params.pop("output_file", None)
        params.pop("output_format", None)

        # obtain output file
        output_file = self._file_system.get_output_file(job_id, output_format)

        # get the configuration for the job_type
        config_file = self._file_system.get_module_file_path(job_type)
        config = json.load(open(config_file, "r"))

        steps = [
            # read the result checkpoint files in the correct order
            ReadPickleStep(self._file_system.iter_results_file_handles(job_id, mode="rb")),
            # don't preprocess, don't do prediction, only post-process based on config
            PostprocessFromConfigStep(
                config=config,
                job_id=job_id,
                output_format=output_format,
                output_file=output_file,
                **params,
            ),
            # send messages to the corresponding topics
            WriteOutputStep(
                output_format="json",
                config=None,  # type: ignore[arg-type]
                channel=self.channel,
                loop=get_running_loop(),
            ),
        ]

        # Run the serialization in a separate thread to avoid blocking the event loop. We don't need
        # to look out for exceptions, because any exception raised in the thread will be re-raised
        # by asyncio here.
        await to_thread(lambda: run_pipeline(*steps))

    async def _process_tombstone(self, message: Tombstone[SerializationRequestMessage]) -> None:
        job_id = message.job_id
        output_format = message.output_format
        logger.info(f"Received tombstone for job {job_id} in format {output_format}")

        # remove the output file if it exists
        output_file = self._file_system.get_output_file(job_id, output_format)
        if os.path.exists(output_file):
            os.remove(output_file)

        await self.channel.serialization_results_topic().send(
            Tombstone(SerializationResultMessage, job_id=job_id, output_format=output_format)
        )
