"""High-level parser for extracting structured data from unstructured log messages."""

import io
from typing import BinaryIO, Generator, TextIO, KeysView

from log_surgeon.group_name_resolver import GroupNameResolver
from log_surgeon.schema_compiler import SchemaCompiler
from log_surgeon.log_event import LogEvent
from log_surgeon_ffi import ReaderParser

_PARSER_NOT_INITIALIZED_ERROR = (
    "Parser not initialized. Load a log surgeon schema using load_schema() or compile()"
)


class Parser:
    """
    High-level parser for extracting structured data from unstructured log messages.

    The Parser uses a schema-based approach to identify patterns, extract variables,
    and generate log types from raw log text. It supports both fluent API style
    (using add_var() and compile()) and direct schema loading.

    Example:
        >>> parser = Parser()
        >>> parser.add_var("metric", r"value=(?<value>\\d+)")
        >>> parser.compile()
        >>> event = parser.parse_event("Processing value=42")
        >>> print(event['value'])
        42
    """

    def __init__(self, delimiters: str = r" \t\r\n:,!;%@/\(\)\[\]") -> None:
        """
        Initialize the parser.

        Args:
            delimiters: String of delimiter characters for tokenization.
                Default includes space, tab, newline, and common punctuation.
                These characters are used to split log messages into tokens.
        """
        self._parser: ReaderParser | None = None
        self._schema_compiler: SchemaCompiler = SchemaCompiler(delimiters)
        self._enable_debug = False

    def add_var(
        self,
        name: str,
        regex: str,
        hide_var_name_if_named_group_present: bool = True
    ) -> "Parser":
        """
        Add a variable pattern to the parser's schema.

        Args:
            name: Variable name
            regex: Regular expression pattern (supports (?<name>) capture groups)
            hide_var_name_if_named_group_present: If True and capture groups exist,
                hide the variable name from output

        Returns:
            Self for method chaining
        """
        self._schema_compiler.add_var(name, regex, hide_var_name_if_named_group_present)
        return self

    def add_timestamp(self, name: str, regex: str) -> "Parser":
        """
        Add a timestamp pattern to the parser's schema.

        Args:
            name: Name identifier for the timestamp pattern
            regex: Regular expression pattern for matching timestamps

        Returns:
            Self for method chaining

        Example:
            >>> parser.add_timestamp("iso8601", r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}")
        """
        self._schema_compiler.add_timestamp(name, regex)
        return self

    def compile(self, enable_debug_logs: bool = False) -> None:
        """
        Build and initialize the parser with the configured schema.

        This method compiles the schema and creates the underlying ReaderParser.
        Must be called after adding variables and before parsing.

        Args:
            enable_debug_logs: If True, output debug information to stderr during
                compilation and parsing operations. Default is False.

        Raises:
            May raise exceptions if schema compilation fails

        Example:
            >>> parser = Parser()
            >>> parser.add_var("metric", r"value=(?<value>\\d+)")
            >>> parser.compile(enable_debug_logs=True)  # Enable debug mode
        """
        self._parser = ReaderParser(
            io.BytesIO(),
            self._schema_compiler.compile(),
            self._schema_compiler.get_capture_group_name_resolver(),
            enable_debug_logs
        )

    def load_schema(self, schema: str, group_name_resolver: GroupNameResolver) -> None:
        """
        Load a schema string to configure the parser.

        Args:
            schema: Schema definition string
            group_name_resolver: GroupNameResolver for mapping logical to physical group names
        """
        self._parser = ReaderParser(io.BytesIO(), schema, group_name_resolver)

    def parse_event(self, payload: str) -> LogEvent | None:
        """
        Parse a single log event from a string payload.

        This is a convenience method that wraps parse() and returns the first event.

        Args:
            payload: Log message string to parse

        Returns:
            Parsed LogEvent or None if no event found

        Raises:
            RuntimeError: If parser is not initialized with a schema

        Example:
            >>> parser = Parser()
            >>> parser.add_var("metric", r"value=(?<value>\\d+)")
            >>> parser.compile()
            >>> event = parser.parse_event("Processing value=42")
            >>> print(event['value'])
            42
        """
        for event in self.parse(payload):
            return event
        return None

    def parse(
        self, input: str | TextIO | BinaryIO | io.StringIO | io.BytesIO
    ) -> Generator[LogEvent, None, None]:
        """
        Parse all log events from an input stream, file object, or string.

        Args:
            input: Input data to parse. Can be:
                - str: Plain string containing log data
                - TextIO: Text file object (opened in text mode)
                - BinaryIO: Binary file object (opened in binary mode)
                - io.StringIO: String buffer
                - io.BytesIO: Bytes buffer

        Yields:
            LogEvent objects for each parsed event

        Raises:
            RuntimeError: If parser is not initialized with a schema
            TypeError: If input type is not supported

        Example:
            >>> parser = Parser()
            >>> parser.add_var("metric", r"value=(?<value>\\d+)")
            >>> parser.compile()
            >>>
            >>> # Parse from string
            >>> for event in parser.parse("value=42\\nvalue=100"):
            ...     print(event['value'])
            >>>
            >>> # Parse from file object
            >>> with open("logs.txt", "r") as f:
            ...     for event in parser.parse(f):
            ...         print(event['value'])
        """
        self._ensure_initialized()

        # Validate and convert input type
        if isinstance(input, str):
            input_stream = io.StringIO(input)
        elif isinstance(input, (io.StringIO, io.BytesIO)):
            input_stream = input
        elif hasattr(input, "read"):
            # Handle file objects (TextIO or BinaryIO)
            content = input.read()
            if isinstance(content, bytes):
                input_stream = io.BytesIO(content)
            elif isinstance(content, str):
                input_stream = io.StringIO(content)
            else:
                raise TypeError(
                    f"File object returned unsupported type {type(content).__name__}"
                )
        else:
            raise TypeError(
                f"Input must be str, file object, io.StringIO, or io.BytesIO, "
                f"got {type(input).__name__}"
            )

        self._parser.reset_input_stream(input_stream)
        while (event := self._parser.parse_next_log_event()) is not None:
            yield event

    def get_vars(self) -> KeysView[str]:
        """
        Get all variable names (logical capture group names) defined in the schema.

        This method returns all the logical names that were defined using add_var()
        or present in the loaded schema. These correspond to the keys available
        in parsed LogEvent objects.

        Returns:
            A view of all variable names defined in the schema

        Example:
            >>> parser = Parser()
            >>> parser.add_var("metric", r"value=(?<value>\\d+)")
            >>> parser.add_var("status", r"status=(?<status>\\w+)")
            >>> parser.compile()
            >>> parser.get_vars()
            dict_keys(['metric', 'status'])
        """
        return self._schema_compiler.get_capture_group_name_resolver().get_all_logical_names()

    def _ensure_initialized(self) -> None:
        """
        Ensure the parser has been initialized with a schema.

        Raises:
            RuntimeError: If parser is not initialized
        """
        if self._parser is None:
            raise RuntimeError(_PARSER_NOT_INITIALIZED_ERROR)


if __name__ == "__main__":
    # Example 1: Extract a single capture group from a log message
    parser = Parser()
    parser.add_var(
        "memoryStore",
        r"MemoryStore started with capacity (?<memory_store_capacity_GiB>\d+\.\d+) GiB"
    )
    parser.compile()

    event = parser.parse_event(
        " INFO [main] MemoryStore: MemoryStore started with capacity 7.0 GiB\n"
    )

    print("Example 1: Basic parsing")
    print(f"Message: {event.get_log_message().strip()}")
    print(f"LogType: {event.get_log_type()}")
    print(f"Capture groups: {event}")
    print()

    # Example 2: Extract multiple capture groups (platform metadata + application data)
    parser = Parser()
    parser.add_var(
        "platform",
        r"(?<platform_level>(INFO)|(WARN)|(ERROR)) \[(?<platform_thread>.+)\] (?<platform_component>.+):"
    )
    parser.add_var(
        "memoryStore",
        r"MemoryStore started with capacity (?<memory_store_capacity_GiB>\d+\.\d+) GiB"
    )
    parser.compile()

    event = parser.parse_event(
        " INFO [main] MemoryStore: MemoryStore started with capacity 7.0 GiB\n"
    )

    print("Example 2: Multiple capture groups")
    print(f"Message: {event.get_log_message().strip()}")
    print(f"LogType: {event.get_log_type()}")
    print(f"Capture groups: {event}")
