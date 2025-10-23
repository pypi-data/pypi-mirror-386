from _typeshed import Incomplete
from gllm_core.constants import EventLevel as EventLevel, EventType as EventType
from gllm_core.event.handler import ConsoleEventHandler as ConsoleEventHandler, PrintEventHandler as PrintEventHandler, StreamEventHandler as StreamEventHandler
from gllm_core.event.handler.event_handler import BaseEventHandler as BaseEventHandler
from gllm_core.event.hook.event_hook import BaseEventHook as BaseEventHook
from gllm_core.schema import Event as Event
from gllm_core.utils import validate_string_enum as validate_string_enum
from typing import Any, AsyncGenerator

class EventEmitter:
    '''Handles events emitting using event handlers with various levels and types.

    The `EventEmitter` class is responsible for handling and emitting events using a list of event handlers.
    Events are processed based on their severity level and type, with the option to disable specific handlers.

    Attributes:
        handlers (list[BaseEventHandler]): A list of event handlers to process emitted events.
        severity (int): The minimum severity level of events to be processed.

    Examples:
        Basic usage:
        ```python
        event_emitter = EventEmitter(handlers=[ConsoleEventHandler()])
        await event_emitter.emit("Hello, world!")
        ```

        Emitting an event object:
        ```python
        event_emitter = EventEmitter(handlers=[ConsoleEventHandler()])
        event = Event(id="123", value="Hello, world!", level=EventLevel.INFO, type="object", metadata={})
        await event_emitter.emit(event)
        ```

        Using with hooks:
        ```python
        event_emitter = EventEmitter(handlers=[ConsoleEventHandler()], hooks=[JSONStringifyEventHook()])
        await event_emitter.emit("Hello, world!")
        ```

        Using with customized event level:
        ```python
        event_emitter = EventEmitter(handlers=[ConsoleEventHandler()], event_level=EventLevel.DEBUG)
        await event_emitter.emit("Hello, world!")
        ```

        Using with console handler:
        ```python
        event_emitter = EventEmitter.with_console_handler()
        await event_emitter.emit("Hello, world!")
        ```

        Using with print handler:
        ```python
        event_emitter = EventEmitter.with_print_handler()
        await event_emitter.emit("Hello, world!")
        ```

        Using with stream handler:
        ```python
        async def function(event_emitter: EventEmitter):
            await event_emitter.emit("Hello, world!")

        event_emitter = EventEmitter.with_stream_handler()
        asyncio.create_task(function(event_emitter))
        async for event in event_emitter.stream():
            print(event)
        ```
    '''
    handlers: Incomplete
    severity: Incomplete
    hooks: Incomplete
    def __init__(self, handlers: list[BaseEventHandler], event_level: EventLevel = ..., hooks: list[BaseEventHook] | None = None) -> None:
        """Initializes a new instance of the EventEmitter class.

        Args:
            handlers (list[BaseEventHandler]): A list of event handlers to process emitted events.
            event_level (EventLevel, optional): The minimum severity level of events to be processed.
                Defaults to EventLevel.INFO.
            hooks (list[BaseEventHook] | None, optional): A list of event hooks to be applied to the emitted events.
                Defaults to None, in which case the event emitter will not apply any hooks.

        Raises:
            ValueError:
                1. If the event handlers list is empty.
                2. If an invalid event level is provided.
        """
    @classmethod
    def with_console_handler(cls, event_level: EventLevel = ..., hooks: list[BaseEventHook] | None = None) -> EventEmitter:
        """Creates a new instance of the EventEmitter class with a single ConsoleEventHandler.

        Args:
            event_level (EventLevel, optional): The minimum severity level of events to be processed.
                Defaults to EventLevel.INFO.
            hooks (list[BaseEventHook] | None, optional): A list of event hooks to be applied to the emitted events.
                Defaults to None, in which case the event emitter will not apply any hooks.

        Returns:
            EventEmitter: A new instance of the EventEmitter class with a single ConsoleEventHandler.
        """
    @classmethod
    def with_print_handler(cls, event_level: EventLevel = ..., hooks: list[BaseEventHook] | None = None) -> EventEmitter:
        """Creates a new instance of the EventEmitter class with a single PrintEventHandler.

        Args:
            event_level (EventLevel, optional): The minimum severity level of events to be processed.
                Defaults to EventLevel.INFO.
            hooks (list[BaseEventHook] | None, optional): A list of event hooks to be applied to the emitted events.
                Defaults to None, in which case the event emitter will not apply any hooks.

        Returns:
            EventEmitter: A new instance of the EventEmitter class with a single PrintEventHandler.
        """
    @classmethod
    def with_stream_handler(cls, event_level: EventLevel = ..., hooks: list[BaseEventHook] | None = None) -> EventEmitter:
        """Creates a new instance of the EventEmitter class with a single StreamEventHandler.

        Args:
            event_level (EventLevel, optional): The minimum severity level of events to be processed.
                Defaults to EventLevel.INFO.
            hooks (list[BaseEventHook] | None, optional): A list of event hooks to be applied to the emitted events.
                Defaults to None, in which case the event emitter will not apply any hooks.

        Returns:
            EventEmitter: A new instance of the EventEmitter class with a single StreamEventHandler.
        """
    async def emit(self, value: str | dict[str, Any] | Event, event_level: EventLevel = ..., event_type: str = ..., metadata: dict[str, Any] | None = None, event_id: str | None = None, disabled_handlers: list[str] | None = None) -> None:
        '''Emits an event using the configured event handlers.

        If the value is an Event object, it is used directly and other parameters are ignored.
        Otherwise, a new Event object is created with the provided parameters. The event is
        then passed to all handlers except those listed in disabled_handlers. Events are only
        processed if their severity level meets or exceeds the EventEmitter\'s configured level.

        Args:
            value (str | dict[str, Any] | Event): The event value or Event object to emit. If an Event object
                is provided, other parameters are ignored and the Event is used as-is.
            event_level (EventLevel, optional): The severity level of the event.
                Defaults to EventLevel.DEBUG.
            event_type (str, optional): The type of event (e.g., "status", "response").
                Defaults to EventType.STATUS.value.
            metadata (dict[str, Any] | None, optional): Additional metadata for the event.
                Defaults to None, which creates an empty dictionary.
            event_id (str | None, optional): Unique identifier for the event.
                Defaults to None, which creates an empty string.
            disabled_handlers (list[str] | None, optional): Names of handlers to skip for
                this event. Defaults to None.

        Raises:
            ValueError: If the provided event_level is not a valid EventLevel.
        '''
    async def close(self) -> None:
        """Closes all handlers in the handler list.

        This method iterates through the list of handlers and calls the `close` method on each handler.

        Returns:
            None
        """
    def stream(self) -> AsyncGenerator:
        """Streams events from the StreamEventHandler.

        This method is a convenience method that calls the `stream` method on the StreamEventHandler.
        To use this method, the event emitter must have exactly one StreamEventHandler.

        Returns:
            AsyncGenerator: An asynchronous generator yielding events from the StreamEventHandler.
        """
