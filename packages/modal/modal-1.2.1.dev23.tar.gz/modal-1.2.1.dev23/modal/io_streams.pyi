import collections.abc
import modal._utils.task_command_router_client
import modal.client
import modal.stream_type
import typing
import typing_extensions

def _sandbox_logs_iterator(
    sandbox_id: str, file_descriptor: int, last_entry_id: str, client: modal.client._Client
) -> collections.abc.AsyncGenerator[tuple[typing.Optional[bytes], str], None]: ...
def _container_process_logs_iterator(
    process_id: str,
    file_descriptor: int,
    client: modal.client._Client,
    last_index: int,
    deadline: typing.Optional[float] = None,
) -> collections.abc.AsyncGenerator[tuple[typing.Optional[bytes], int], None]: ...

T = typing.TypeVar("T")

class _StreamReaderThroughServer(typing.Generic[T]):
    """A StreamReader implementation that reads from the server."""

    _stream: typing.Optional[collections.abc.AsyncGenerator[T, None]]

    def __init__(
        self,
        file_descriptor: int,
        object_id: str,
        object_type: typing.Literal["sandbox", "container_process"],
        client: modal.client._Client,
        stream_type: modal.stream_type.StreamType = modal.stream_type.StreamType.PIPE,
        text: bool = True,
        by_line: bool = False,
        deadline: typing.Optional[float] = None,
    ) -> None:
        """mdmd:hidden"""
        ...

    @property
    def file_descriptor(self) -> int:
        """Possible values are `1` for stdout and `2` for stderr."""
        ...

    async def read(self) -> T:
        """Fetch the entire contents of the stream until EOF."""
        ...

    async def _consume_container_process_stream(self):
        """Consume the container process stream and store messages in the buffer."""
        ...

    def _stream_container_process(self) -> collections.abc.AsyncGenerator[tuple[typing.Optional[bytes], str], None]:
        """Streams the container process buffer to the reader."""
        ...

    def _get_logs(self, skip_empty_messages: bool = True) -> collections.abc.AsyncGenerator[bytes, None]:
        """Streams sandbox or process logs from the server to the reader.

        Logs returned by this method may contain partial or multiple lines at a time.

        When the stream receives an EOF, it yields None. Once an EOF is received,
        subsequent invocations will not yield logs.
        """
        ...

    def _get_logs_by_line(self) -> collections.abc.AsyncGenerator[bytes, None]:
        """Process logs from the server and yield complete lines only."""
        ...

    def _ensure_stream(self) -> collections.abc.AsyncGenerator[T, None]: ...
    async def __anext__(self) -> T:
        """mdmd:hidden"""
        ...

    async def aclose(self):
        """mdmd:hidden"""
        ...

def _decode_bytes_stream_to_str(
    stream: collections.abc.AsyncGenerator[bytes, None],
) -> collections.abc.AsyncGenerator[str, None]:
    """Incrementally decode a bytes async generator as UTF-8 without breaking on chunk boundaries.

    This function uses a streaming UTF-8 decoder so that multi-byte characters split across
    chunks are handled correctly instead of raising ``UnicodeDecodeError``.
    """
    ...

def _stream_by_line(stream: collections.abc.AsyncGenerator[bytes, None]) -> collections.abc.AsyncGenerator[bytes, None]:
    """Yield complete lines only (ending with
    ), buffering partial lines until complete.
    """
    ...

class _StreamReaderThroughCommandRouterParams:
    """_StreamReaderThroughCommandRouterParams(file_descriptor: 'api_pb2.FileDescriptor.ValueType', task_id: str, object_id: str, command_router_client: modal._utils.task_command_router_client.TaskCommandRouterClient, deadline: Optional[float])"""

    file_descriptor: int
    task_id: str
    object_id: str
    command_router_client: modal._utils.task_command_router_client.TaskCommandRouterClient
    deadline: typing.Optional[float]

    def __init__(
        self,
        file_descriptor: int,
        task_id: str,
        object_id: str,
        command_router_client: modal._utils.task_command_router_client.TaskCommandRouterClient,
        deadline: typing.Optional[float],
    ) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        ...

    def __repr__(self):
        """Return repr(self)."""
        ...

    def __eq__(self, other):
        """Return self==value."""
        ...

def _stdio_stream_from_command_router(
    params: _StreamReaderThroughCommandRouterParams,
) -> collections.abc.AsyncGenerator[bytes, None]:
    """Stream raw bytes from the router client."""
    ...

class _BytesStreamReaderThroughCommandRouter(typing.Generic[T]):
    """StreamReader implementation that will read directly from the worker that
    hosts the sandbox.

    This implementation is used for non-text streams.
    """
    def __init__(self, params: _StreamReaderThroughCommandRouterParams) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        ...

    @property
    def file_descriptor(self) -> int: ...
    async def read(self) -> T: ...
    def __aiter__(self) -> collections.abc.AsyncIterator[T]: ...
    async def __anext__(self) -> T: ...
    async def aclose(self): ...

class _TextStreamReaderThroughCommandRouter(typing.Generic[T]):
    """StreamReader implementation that will read directly from the worker
    that hosts the sandbox.

    This implementation is used for text streams.
    """
    def __init__(self, params: _StreamReaderThroughCommandRouterParams, by_line: bool) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        ...

    @property
    def file_descriptor(self) -> int: ...
    async def read(self) -> T: ...
    def __aiter__(self) -> collections.abc.AsyncIterator[T]: ...
    async def __anext__(self) -> T: ...
    async def aclose(self): ...

class _DevnullStreamReader(typing.Generic[T]):
    """StreamReader implementation for a stream configured with
    StreamType.DEVNULL. Throws an error if read or any other method is
    called.
    """
    def __init__(self, file_descriptor: int) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        ...

    @property
    def file_descriptor(self) -> int: ...
    async def read(self) -> T: ...
    def __aiter__(self) -> collections.abc.AsyncIterator[T]: ...
    async def __anext__(self) -> T: ...
    async def aclose(self): ...

class _StreamReader(typing.Generic[T]):
    """Retrieve logs from a stream (`stdout` or `stderr`).

    As an asynchronous iterable, the object supports the `for` and `async for`
    statements. Just loop over the object to read in chunks.

    **Usage**

    ```python fixture:running_app
    from modal import Sandbox

    sandbox = Sandbox.create(
        "bash",
        "-c",
        "for i in $(seq 1 10); do echo foo; sleep 0.1; done",
        app=running_app,
    )
    for message in sandbox.stdout:
        print(f"Message: {message}")
    ```
    """
    def __init__(
        self,
        file_descriptor: int,
        object_id: str,
        object_type: typing.Literal["sandbox", "container_process"],
        client: modal.client._Client,
        stream_type: modal.stream_type.StreamType = modal.stream_type.StreamType.PIPE,
        text: bool = True,
        by_line: bool = False,
        deadline: typing.Optional[float] = None,
        command_router_client: typing.Optional[modal._utils.task_command_router_client.TaskCommandRouterClient] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        """mdmd:hidden"""
        ...

    @property
    def file_descriptor(self) -> int:
        """Possible values are `1` for stdout and `2` for stderr."""
        ...

    async def read(self) -> T:
        """Fetch the entire contents of the stream until EOF.

        **Usage**

        ```python fixture:running_app
        from modal import Sandbox

        sandbox = Sandbox.create("echo", "hello", app=running_app)
        sandbox.wait()

        print(sandbox.stdout.read())
        ```
        """
        ...

    def __aiter__(self) -> collections.abc.AsyncIterator[T]:
        """mdmd:hidden"""
        ...

    async def __anext__(self) -> T:
        """mdmd:hidden"""
        ...

    async def aclose(self):
        """mdmd:hidden"""
        ...

class _StreamWriterThroughServer:
    """Provides an interface to buffer and write logs to a sandbox or container process stream (`stdin`)."""
    def __init__(
        self, object_id: str, object_type: typing.Literal["sandbox", "container_process"], client: modal.client._Client
    ) -> None:
        """mdmd:hidden"""
        ...

    def _get_next_index(self) -> int: ...
    def write(self, data: typing.Union[bytes, bytearray, memoryview, str]) -> None:
        """Write data to the stream but does not send it immediately.

        This is non-blocking and queues the data to an internal buffer. Must be
        used along with the `drain()` method, which flushes the buffer.
        """
        ...

    def write_eof(self) -> None:
        """Close the write end of the stream after the buffered data is drained.

        If the process was blocked on input, it will become unblocked after
        `write_eof()`. This method needs to be used along with the `drain()`
        method, which flushes the EOF to the process.
        """
        ...

    async def drain(self) -> None:
        """Flush the write buffer and send data to the running process.

        This is a flow control method that blocks until data is sent. It returns
        when it is appropriate to continue writing data to the stream.
        """
        ...

class _StreamWriterThroughCommandRouter:
    def __init__(
        self,
        object_id: str,
        command_router_client: modal._utils.task_command_router_client.TaskCommandRouterClient,
        task_id: str,
    ) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        ...

    def write(self, data: typing.Union[bytes, bytearray, memoryview, str]) -> None: ...
    def write_eof(self) -> None: ...
    async def drain(self) -> None: ...

class _StreamWriter:
    """Provides an interface to buffer and write logs to a sandbox or container process stream (`stdin`)."""
    def __init__(
        self,
        object_id: str,
        object_type: typing.Literal["sandbox", "container_process"],
        client: modal.client._Client,
        command_router_client: typing.Optional[modal._utils.task_command_router_client.TaskCommandRouterClient] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        """mdmd:hidden"""
        ...

    def write(self, data: typing.Union[bytes, bytearray, memoryview, str]) -> None:
        """Write data to the stream but does not send it immediately.

        This is non-blocking and queues the data to an internal buffer. Must be
        used along with the `drain()` method, which flushes the buffer.

        **Usage**

        ```python fixture:running_app
        from modal import Sandbox

        sandbox = Sandbox.create(
            "bash",
            "-c",
            "while read line; do echo $line; done",
            app=running_app,
        )
        sandbox.stdin.write(b"foo\n")
        sandbox.stdin.write(b"bar\n")
        sandbox.stdin.write_eof()

        sandbox.stdin.drain()
        sandbox.wait()
        ```
        """
        ...

    def write_eof(self) -> None:
        """Close the write end of the stream after the buffered data is drained.

        If the process was blocked on input, it will become unblocked after
        `write_eof()`. This method needs to be used along with the `drain()`
        method, which flushes the EOF to the process.
        """
        ...

    async def drain(self) -> None:
        """Flush the write buffer and send data to the running process.

        This is a flow control method that blocks until data is sent. It returns
        when it is appropriate to continue writing data to the stream.

        **Usage**

        ```python notest
        writer.write(data)
        writer.drain()
        ```

        Async usage:
        ```python notest
        writer.write(data)  # not a blocking operation
        await writer.drain.aio()
        ```
        """
        ...

T_INNER = typing.TypeVar("T_INNER", covariant=True)

SUPERSELF = typing.TypeVar("SUPERSELF", covariant=True)

class StreamReader(typing.Generic[T]):
    """Retrieve logs from a stream (`stdout` or `stderr`).

    As an asynchronous iterable, the object supports the `for` and `async for`
    statements. Just loop over the object to read in chunks.

    **Usage**

    ```python fixture:running_app
    from modal import Sandbox

    sandbox = Sandbox.create(
        "bash",
        "-c",
        "for i in $(seq 1 10); do echo foo; sleep 0.1; done",
        app=running_app,
    )
    for message in sandbox.stdout:
        print(f"Message: {message}")
    ```
    """
    def __init__(
        self,
        file_descriptor: int,
        object_id: str,
        object_type: typing.Literal["sandbox", "container_process"],
        client: modal.client.Client,
        stream_type: modal.stream_type.StreamType = modal.stream_type.StreamType.PIPE,
        text: bool = True,
        by_line: bool = False,
        deadline: typing.Optional[float] = None,
        command_router_client: typing.Optional[modal._utils.task_command_router_client.TaskCommandRouterClient] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        """mdmd:hidden"""
        ...

    @property
    def file_descriptor(self) -> int:
        """Possible values are `1` for stdout and `2` for stderr."""
        ...

    class __read_spec(typing_extensions.Protocol[T_INNER, SUPERSELF]):
        def __call__(self, /) -> T_INNER:
            """Fetch the entire contents of the stream until EOF.

            **Usage**

            ```python fixture:running_app
            from modal import Sandbox

            sandbox = Sandbox.create("echo", "hello", app=running_app)
            sandbox.wait()

            print(sandbox.stdout.read())
            ```
            """
            ...

        async def aio(self, /) -> T_INNER:
            """Fetch the entire contents of the stream until EOF.

            **Usage**

            ```python fixture:running_app
            from modal import Sandbox

            sandbox = Sandbox.create("echo", "hello", app=running_app)
            sandbox.wait()

            print(sandbox.stdout.read())
            ```
            """
            ...

    read: __read_spec[T, typing_extensions.Self]

    def __iter__(self) -> typing.Iterator[T]:
        """mdmd:hidden"""
        ...

    def __aiter__(self) -> collections.abc.AsyncIterator[T]:
        """mdmd:hidden"""
        ...

    def __next__(self) -> T:
        """mdmd:hidden"""
        ...

    async def __anext__(self) -> T:
        """mdmd:hidden"""
        ...

    def close(self):
        """mdmd:hidden"""
        ...

    async def aclose(self):
        """mdmd:hidden"""
        ...

class StreamWriter:
    """Provides an interface to buffer and write logs to a sandbox or container process stream (`stdin`)."""
    def __init__(
        self,
        object_id: str,
        object_type: typing.Literal["sandbox", "container_process"],
        client: modal.client.Client,
        command_router_client: typing.Optional[modal._utils.task_command_router_client.TaskCommandRouterClient] = None,
        task_id: typing.Optional[str] = None,
    ) -> None:
        """mdmd:hidden"""
        ...

    def write(self, data: typing.Union[bytes, bytearray, memoryview, str]) -> None:
        """Write data to the stream but does not send it immediately.

        This is non-blocking and queues the data to an internal buffer. Must be
        used along with the `drain()` method, which flushes the buffer.

        **Usage**

        ```python fixture:running_app
        from modal import Sandbox

        sandbox = Sandbox.create(
            "bash",
            "-c",
            "while read line; do echo $line; done",
            app=running_app,
        )
        sandbox.stdin.write(b"foo\n")
        sandbox.stdin.write(b"bar\n")
        sandbox.stdin.write_eof()

        sandbox.stdin.drain()
        sandbox.wait()
        ```
        """
        ...

    def write_eof(self) -> None:
        """Close the write end of the stream after the buffered data is drained.

        If the process was blocked on input, it will become unblocked after
        `write_eof()`. This method needs to be used along with the `drain()`
        method, which flushes the EOF to the process.
        """
        ...

    class __drain_spec(typing_extensions.Protocol[SUPERSELF]):
        def __call__(self, /) -> None:
            """Flush the write buffer and send data to the running process.

            This is a flow control method that blocks until data is sent. It returns
            when it is appropriate to continue writing data to the stream.

            **Usage**

            ```python notest
            writer.write(data)
            writer.drain()
            ```

            Async usage:
            ```python notest
            writer.write(data)  # not a blocking operation
            await writer.drain.aio()
            ```
            """
            ...

        async def aio(self, /) -> None:
            """Flush the write buffer and send data to the running process.

            This is a flow control method that blocks until data is sent. It returns
            when it is appropriate to continue writing data to the stream.

            **Usage**

            ```python notest
            writer.write(data)
            writer.drain()
            ```

            Async usage:
            ```python notest
            writer.write(data)  # not a blocking operation
            await writer.drain.aio()
            ```
            """
            ...

    drain: __drain_spec[typing_extensions.Self]
