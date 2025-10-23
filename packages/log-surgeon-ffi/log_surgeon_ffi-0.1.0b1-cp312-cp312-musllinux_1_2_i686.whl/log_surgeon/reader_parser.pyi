from typing import IO, Union

from log_event import LogEvent
from group_name_resolver import GroupNameResolver

class ReaderParser:
    def __init__(
        self,
        input_stream: IO[bytes],
        schema_content: str,
        group_name_resolver: GroupNameResolver,
        debug: bool = False
    ) -> None: ...
    def parse_next_log_event(self) -> Union[LogEvent, None]: ...
    def reset_input_stream(self, input_stream: IO[bytes]) -> bool: ...
    def done(self) -> bool: ...
