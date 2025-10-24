# Copyright 2025 Eli Lilly and Company
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module for handling output files."""

from __future__ import annotations

import logging
from queue import Queue
from sys import exc_info
from threading import Thread
from typing import TYPE_CHECKING, cast

from zarr import open_group

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from zarr import Array


def _writer(site: str, queue: Queue, group_path: Path, error_queue: Queue) -> None:
    """Background worker that writes posterior predictive samples to a Zarr array.

    This function runs in a loop, retrieving posterior predictive samples as arrays from
    the queue and appending them to the appropriate dataset in the given Zarr group
    along the sample (second) axis. It exits when a ``None`` sentinel value is received.
    If an error occurs while writing to the Zarr array, it is logged and the error
    details are put into the ``error_queue``.

    Args:
        site: The name of the sample site.
        queue: The queue to retrieve posterior predictive samples from.
        group_path: The path to the Zarr group where data will be written.
        error_queue: The queue to collect errors raised by the writer thread.
    """
    group = open_group(group_path, mode="r+")

    while True:
        arr = queue.get()
        if arr is None:
            queue.task_done()
            break

        try:
            cast("Array", group[site]).append(arr, axis=1)
        except Exception as e:
            msg = f"Error writing to site '{site}': {e}"
            logger.exception(msg)
            _, exc_value, exc_tb = exc_info()
            error_queue.put((site, exc_value, exc_tb))
            # Drain remaining items including sentinel
            while True:
                leftover = queue.get()
                queue.task_done()
                if leftover is None:
                    break

            break
        finally:
            queue.task_done()


def _start_writer_threads(
    sites: tuple[str, ...],
    group_path: Path,
    writer: Callable[[str, Queue, Path, Queue], None],
    queue_size: int,
) -> tuple[list[Thread], dict[str, Queue], Queue]:
    """Start writer threads and their corresponding queues for each site.

    Args:
        sites: Names of the return sites.
        group_path: The path to the Zarr group where data will be written.
        writer: The function that processes queued data and writes to Zarr.
        queue_size: Maximum size of each queue (per site).

    Returns:
        A tuple containing a list of threads and a dictionary mapping each site to its
        corresponding queue.
    """
    queues: dict[str, Queue] = {site: Queue(queue_size) for site in sites}
    threads = []
    error_queue: Queue = Queue()
    for site, queue in queues.items():
        thread = Thread(target=writer, args=(site, queue, group_path, error_queue))
        thread.start()
        threads.append(thread)

    return threads, queues, error_queue


def _shutdown_writer_threads(
    threads: list[Thread],
    queues: dict[str, Queue],
) -> None:
    """Signal writer threads to stop and wait for their completion.

    Args:
        threads: List of writer threads to join.
        queues: Mapping of site names to their respective queues.
        error_queue: Queue to collect errors raised by writer threads.
    """
    for queue in queues.values():
        queue.put(None)
    for queue in queues.values():
        queue.join()
    for thread in threads:
        thread.join()
