# src/pico_ioc/exceptions.py
from typing import Any, Iterable

class PicoError(Exception):
    pass

class ProviderNotFoundError(PicoError):
    def __init__(self, key: Any):
        super().__init__(f"Provider not found for key: {getattr(key, '__name__', key)}")
        self.key = key

class CircularDependencyError(PicoError):
    def __init__(self, chain: Iterable[Any], current: Any):
        chain_str = " -> ".join(getattr(k, "__name__", str(k)) for k in chain)
        cur_str = getattr(current, "__name__", str(current))
        super().__init__(f"Circular dependency detected: {chain_str} -> {cur_str}")
        self.chain = tuple(chain)
        self.current = current

class ComponentCreationError(PicoError):
    def __init__(self, key: Any, cause: Exception):
        k = getattr(key, "__name__", key)
        super().__init__(f"Failed to create component for key: {k}; cause: {cause.__class__.__name__}: {cause}")
        self.key = key
        self.cause = cause

class ScopeError(PicoError):
    def __init__(self, msg: str):
        super().__init__(msg)

class ConfigurationError(PicoError):
    def __init__(self, msg: str):
        super().__init__(msg)

class SerializationError(PicoError):
    def __init__(self, msg: str):
        super().__init__(msg)

class ValidationError(PicoError):
    def __init__(self, msg: str):
        super().__init__(msg)

class InvalidBindingError(ValidationError):
    def __init__(self, errors: list[str]):
        super().__init__("Invalid bindings:\n" + "\n".join(f"- {e}" for e in errors))
        self.errors = errors

class EventBusError(PicoError):
    def __init__(self, msg: str):
        super().__init__(msg)

class EventBusClosedError(EventBusError):
    def __init__(self):
        super().__init__("EventBus is closed")

class EventBusQueueFullError(EventBusError):
    def __init__(self):
        super().__init__("Event queue is full")

class EventBusHandlerError(EventBusError):
    def __init__(self, event_name: str, handler_name: str, cause: Exception):
        super().__init__(f"Handler {handler_name} failed for event {event_name}: {cause.__class__.__name__}: {cause}")
        self.event_name = event_name
        self.handler_name = handler_name
        self.cause = cause

