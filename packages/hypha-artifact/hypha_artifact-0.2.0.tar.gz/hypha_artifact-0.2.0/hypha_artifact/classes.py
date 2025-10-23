"""Represents a file or directory in the artifact storage."""

from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

OnError = Literal["raise", "ignore"]
JsonType = (
    str
    | int
    | float
    | bool
    | None
    | dict[str, object]
    | list[object]
    | Sequence[object]
    | Mapping[str, object]
)
ListChildrenMode = Literal["AND", "OR"]


class ArtifactItem(TypedDict):
    """Represents an item in the artifact, containing metadata and content."""

    name: str
    type: Literal["file", "directory"]
    size: int
    last_modified: float | None


class FileInfoEvent(TypedDict):
    """File operation event."""

    type: Literal["info"]
    message: str
    file: str
    total_files: int
    current_file: int


class FileSuccessEvent(TypedDict):
    """File success event."""

    type: Literal["success"]
    message: str
    file: str


class FileErrorEvent(TypedDict):
    """File error event."""

    type: Literal["error"]
    message: str
    file: str


class PartInfoEvent(TypedDict, total=False):
    """Part info event."""

    type: Literal["part_info"]
    message: str
    file: str
    current_part: int
    total_parts: int
    part_size: int | None


class PartSuccessEvent(TypedDict, total=False):
    """Part success event."""

    type: Literal["part_success"]
    message: str
    file: str
    current_part: int
    total_parts: int
    part_size: int | None


class PartErrorEvent(TypedDict):
    """Part error event."""

    type: Literal["part_error"]
    message: str
    file: str
    current_part: int
    total_parts: int


ProgressEvent = (
    FileInfoEvent
    | FileSuccessEvent
    | FileErrorEvent
    | PartInfoEvent
    | PartSuccessEvent
    | PartErrorEvent
)

ProgressType = Literal[
    "info",
    "success",
    "error",
    "part_info",
    "part_success",
    "part_error",
    None,
]


class StatusMessage:
    """Class to represent a status message for file operations."""

    def __init__(self, operation: str, total_files: int) -> None:
        """Initialize a status message.

        Args:
            operation (str): The operation being performed (e.g., "upload", "download").
            total_files (int): The total number of files involved in the operation.

        """
        self.operation = operation
        self.total_files = total_files

    def in_progress(
        self: "StatusMessage",
        file_path: str,
        current_file_index: int,
    ) -> FileInfoEvent:
        """Create a message indicating the progress of an operation."""
        return {
            "type": "info",
            "message": (
                f"{self.operation.capitalize()}ing file"
                f" {current_file_index + 1}/{self.total_files}: {file_path}"
            ),
            "file": file_path,
            "total_files": self.total_files,
            "current_file": current_file_index + 1,
        }

    def success(self: "StatusMessage", file_path: str) -> FileSuccessEvent:
        """Create a message indicating a successful operation."""
        return {
            "type": "success",
            "message": f"Successfully {self.operation}ed: {file_path}",
            "file": file_path,
        }

    def error(
        self: "StatusMessage",
        file_path: str,
        error_message: str,
    ) -> FileErrorEvent:
        """Create a message indicating an error during the operation."""
        return {
            "type": "error",
            "message": f"Failed to {self.operation} {file_path}: {error_message}",
            "file": file_path,
        }


class MultipartStatusMessage(StatusMessage):
    """Status messages for multipart uploads at per-part granularity."""

    def __init__(self, operation: str, file_path: str, total_parts: int) -> None:
        """Initialize with operation, target file path, and total parts."""
        super().__init__(operation, total_parts)
        self.file_path = file_path
        self.total_parts = total_parts

    def part_info(
        self,
        part_number: int,
        part_size: int | None = None,
    ) -> PartInfoEvent:
        """Create an in-progress message for a given part."""
        msg = (
            f"{self.operation.capitalize()}ing part {part_number}/{self.total_parts}"
            f" for {self.file_path}"
        )
        return PartInfoEvent(
            type="part_info",
            message=msg,
            file=self.file_path,
            current_part=part_number,
            total_parts=self.total_parts,
            part_size=part_size,
        )

    def part_success(
        self,
        part_number: int,
        part_size: int | None = None,
    ) -> PartSuccessEvent:
        """Create a success message for a completed part."""
        return PartSuccessEvent(
            type="part_success",
            message=(
                f"Successfully {self.operation}ed part {part_number}/{self.total_parts}"
                f" for {self.file_path}"
            ),
            file=self.file_path,
            current_part=part_number,
            total_parts=self.total_parts,
            part_size=part_size,
        )

    def part_error(
        self,
        part_number: int,
        error_message: str,
    ) -> PartErrorEvent:
        """Create an error message for a part failure."""
        return {
            "type": "part_error",
            "message": (
                f"Failed to {self.operation} part {part_number}/{self.total_parts}"
                f" for {self.file_path}: {error_message}"
            ),
            "file": self.file_path,
            "current_part": part_number,
            "total_parts": self.total_parts,
        }


class UploadPartServerInfo(TypedDict):
    """Server-provided info for a part to upload."""

    url: str
    part_number: int


class MultipartConfig(TypedDict, total=False):
    """Configuration for multipart uploads."""

    chunk_size: int
    enable: bool
    threshold: int
    max_parallel_uploads: int


class MultipartUpload(TypedDict):
    """Multipart upload information."""

    upload_id: str
    parts: list[UploadPartServerInfo]
