from typing import Any, Literal, Optional, Protocol, Union
from langchain_core.messages import ToolMessageChunk
from langgraph.config import get_stream_writer
from pydantic import Field


class ToolChunkWriter(Protocol):
    def __call__(
        self,
        *,
        artifact: Any = None,
        status: Literal["success", "error"] = "success",
        content: Union[str, list[Union[str, dict]]],
        response_metadata: dict = Field(default_factory=dict),
        name: Optional[str] = None,
    ) -> None: ...


def get_tool_chunk_writer(tool_call_id: str) -> ToolChunkWriter:
    stream_writer = get_stream_writer()

    def write_chunk(
        *,
        artifact: Any = None,
        status: Literal["success", "error"] = "success",
        content: Union[str, list[Union[str, dict]]],
        response_metadata: dict = {},
        name: Optional[str] = None
    ):
        chunk = ToolMessageChunk(
            id=tool_call_id,
            tool_call_id=tool_call_id,
            artifact=artifact,
            status=status,
            content=content,
            response_metadata=response_metadata,
            name=name,
        )

        stream_writer(chunk)

    return write_chunk


__all__ = ["ToolChunkWriter", "get_tool_chunk_writer"]
