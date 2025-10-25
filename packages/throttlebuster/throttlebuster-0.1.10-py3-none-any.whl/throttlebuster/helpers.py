"""Supportive functions"""

import logging
import typing as t
import warnings

import tqdm

from throttlebuster.constants import ILLEGAL_CHARACTERS_PATTERN

logger = logging.getLogger(__name__)

warnings.simplefilter("ignore", category=(tqdm.std.TqdmWarning,))
"""Raised due to frac*"""


class CustomTqdm(tqdm.tqdm):
    """Formats `n` and `total` bar values"""

    @staticmethod
    def prettify_number(number: float) -> float:
        return round(number, 2)

    @property
    def format_dict(self) -> dict:
        prev_dict = super().format_dict
        prev_dict["n"] = self.prettify_number(prev_dict.get("n"))
        prev_dict["total"] = self.prettify_number(prev_dict.get("total"))

        return prev_dict

    def update(self, n=1):
        # avoid progresbar from surpassing 100%
        # It's not so much effective due to async nature

        # It's particularly useful when range load has not been
        # specified in request headers e.g "Range : bytes=0-" instead of
        # "Range : bytes=0-5000"

        if self.disable:
            return

        if self.last_print_n >= self.total:
            return

        if self.last_print_n + n > self.total:
            return super().update(self.total - self.last_print_n)

        return super().update(n)


class DownloadUtils:
    @classmethod
    def bytes_to_mb(self, bytes: int) -> int:
        return round(bytes / 1_000_000, 6)

    @classmethod
    def get_offset_load(
        cls, content_length: int, tasks: int
    ) -> list[tuple[int, int]]:
        """Determines the bytes offset and the download size of each task

        Args:
            content_length (int): Size of file to be downloaded in bytes.
            tasks (int): Number of tasks for running the download.

        Returns:
            list[tuple[int, int]]: Byte offset & download size per task
        """
        assert tasks > 0, f"Threads value {tasks} should be at least 1"
        assert content_length > 0, (
            f"Content-length value {content_length} should be more than 0"
        )
        assert tasks < content_length, (
            f"Threads amount {tasks} should not be more than "
            f"content_length {content_length}"
        )

        # Calculate base size and distribute remainder to first few chunks
        base_size = content_length // tasks
        remainder = content_length % tasks
        load = [
            base_size + (1 if i < remainder else 0) for i in range(tasks)
        ]

        assert sum(load) == content_length, (
            "Chunk sizes don't add up to total length"
        )
        assert len(load) == tasks, "Wrong number of chunks generated"

        # Generate (start_offset, chunk_size) pairs
        offset_load_container: list[tuple[int, int]] = []
        start = 0

        for size in load:
            offset_load_container.append((start, size))
            start += size

        return offset_load_container

    @classmethod
    def get_filename_from_header(cls, headers: dict) -> str | None:
        """Extracts filename from httpx response headers

        Args:
            headers (dict): Httpx response headers

        Returns:
            str | None: Extracted filename or None
        """
        disposition: str = headers.get("content-disposition")

        if disposition is not None:
            _, filename = disposition.split("filename=")
            return filename


def assert_instance(
    obj: object, class_or_tuple, name: str = "Parameter"
) -> t.NoReturn:
    """assert obj an instance of class_or_tuple"""

    assert isinstance(obj, class_or_tuple), (
        f"{name} value needs to be an instance of/any of {class_or_tuple} "
        f"not {type(obj)}"
    )


def get_filesize_string(size_in_bytes: int) -> str:
    """Get something like `343 MB` or `1.25 GB` depending on sizes."""
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    for unit in units:
        # 1024 or 1000 ?
        if size_in_bytes >= 1000.0:
            size_in_bytes /= 1000.0
        else:
            break

    return f"{size_in_bytes:.2f} {unit}"


def get_duration_string(time_in_seconds: int) -> str:
    """Get something like `2 Mins` or `3 Secs` depending on time."""
    units = ["Secs", "Mins", "Hrs"]

    for unit in units:
        if time_in_seconds >= 60.0:
            time_in_seconds /= 60.0
        else:
            break

    return f"{time_in_seconds:.2f} {unit}"


def sanitize_filename(filename: str) -> str:
    """Remove illegal characters from a filename"""
    return ILLEGAL_CHARACTERS_PATTERN.sub("", filename.replace(":", "-"))
