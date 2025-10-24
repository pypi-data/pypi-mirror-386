# Cookbook: Pattern: Structured Logging with AOP

**Goal:** Automatically add structured (e.g., JSON) logs before and after key service method calls, including contextual information like `request_id` or `user_id` without manually passing it everywhere.

**Key `pico-ioc` Features:** AOP (`MethodInterceptor`, `@intercepted_by`), Scopes (`@scope("request")`), Component Injection into Interceptors.

## The Pattern

1.  **Context Holder (`RequestContext`):** A `@component` with `@scope("request")` to store data specific to the current request (like `request_id`, `user_id`). This would be populated by middleware in a web app.
2.  **Structured Logger (`JsonLogger`):** (Optional) A helper component for formatting logs consistently as JSON.
3.  **Logging Interceptor (`LoggingInterceptor`):** A `@component` implementing `MethodInterceptor`. It:
    * Injects the `RequestContext` and `JsonLogger`.
    * Reads method call details from `ctx` (`class_name`, `method_name`, `args`).
    * Reads context details from `RequestContext`.
    * Logs entry ("before") event in structured format.
    * Calls `call_next(ctx)`.
    * Logs exit ("after") event (including result or exception) in structured format.
4.  **Alias (`log_calls`):** An alias for `@intercepted_by(LoggingInterceptor)`.
5.  **Application:** Service classes or specific methods are decorated with `@log_calls`.

## Full, Runnable Example

### 1. Project Structure
```

.
├── logging\_lib/
│   ├── **init**.py
│   ├── context.py     \<-- RequestContext
│   ├── interceptor.py \<-- LoggingInterceptor & log\_calls alias
│   └── logger.py      \<-- JsonLogger (optional helper)
├── my\_app/
│   ├── **init**.py
│   └── services.py    \<-- Example service using @log\_calls
└── main.py              \<-- Simulation entrypoint

```

### 2. Logging Library (`logging_lib/`)

#### Context (`context.py`)
```python
# logging_lib/context.py
from dataclasses import dataclass
from pico_ioc import component, scope

@component
@scope("request")
@dataclass
class RequestContext:
    request_id: str | None = None
    user_id: str | None = None

    def load(self, request_id: str, user_id: str | None = None):
        self.request_id = request_id
        self.user_id = user_id
        print(f"[Context] Loaded RequestContext: ID={request_id}, User={user_id}")
```

#### Logger (`logger.py`) - Optional Helper

```python
# logging_lib/logger.py
import json
import logging
from pico_ioc import component

log = logging.getLogger("StructuredLogger")
logging.basicConfig(level=logging.INFO, format='%(message)s') # Simple format for demo

@component
class JsonLogger:
    def log(self, event: str, **kwargs):
        log_entry = {"event": event, **kwargs}
        log.info(json.dumps(log_entry, default=str)) # Use default=str for non-serializable args
```

#### Interceptor & Alias (`interceptor.py`)

```python
# logging_lib/interceptor.py
import time
from typing import Any, Callable
from pico_ioc import component, MethodInterceptor, MethodCtx, intercepted_by
from .context import RequestContext
from .logger import JsonLogger # Use our helper

@component
class LoggingInterceptor(MethodInterceptor):
    def __init__(self, context: RequestContext, logger: JsonLogger):
        self.context = context
        self.logger = logger
        print("[Interceptor] LoggingInterceptor initialized.")

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        start_time = time.perf_counter()
        log_context = {
            "request_id": self.context.request_id,
            "user_id": self.context.user_id,
            "class": ctx.cls.__name__,
            "method": ctx.name,
            # Avoid logging large args/kwargs in production if sensitive/large
            # "args": ctx.args,
            # "kwargs": ctx.kwargs
        }

        self.logger.log("method_entry", **log_context)
        
        try:
            result = call_next(ctx)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            log_context["duration_ms"] = round(duration_ms, 2)
            # Avoid logging large results
            # log_context["result"] = result 
            self.logger.log("method_exit", status="success", **log_context)
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_context["duration_ms"] = round(duration_ms, 2)
            log_context["exception_type"] = type(e).__name__
            log_context["exception_message"] = str(e)
            self.logger.log("method_exit", status="failure", **log_context)
            raise # Important: re-raise the exception

# Define the alias
log_calls = intercepted_by(LoggingInterceptor)
```

#### Library `__init__.py`

```python
# logging_lib/__init__.py
from .context import RequestContext
from .interceptor import LoggingInterceptor, log_calls
from .logger import JsonLogger

__all__ = ["RequestContext", "LoggingInterceptor", "log_calls", "JsonLogger"]
```

### 3\. Application Code (`my_app/services.py`)

```python
# my_app/services.py
from pico_ioc import component
from logging_lib import log_calls # Import the alias

@component
@log_calls # Apply the interceptor to the whole class
class OrderService:
    def create_order(self, user_id: str, item: str):
        print(f"  [OrderService] Creating order for {user_id} - item: {item}")
        # Simulate work
        time.sleep(0.05)
        if item == "error":
             raise ValueError("Invalid item specified")
        return {"order_id": "ORD123"}

    def get_order_status(self, order_id: str):
        print(f"  [OrderService] Getting status for {order_id}")
        time.sleep(0.02)
        return "Shipped"
```

### 4\. Main Application (`main.py`)

```python
# main.py
import uuid
from pico_ioc import init
from my_app.services import OrderService
from logging_lib import RequestContext

def run_simulation():
    print("--- Initializing Container ---")
    container = init(modules=["my_app", "logging_lib"])
    print("--- Container Initialized ---\n")

    # --- Simulate Request 1 ---
    req_id_1 = f"req-{uuid.uuid4().hex[:4]}"
    print(f"--- SIMULATING REQUEST {req_id_1} (User: alice) ---")
    with container.scope("request", req_id_1):
        ctx = container.get(RequestContext)
        ctx.load(request_id=req_id_1, user_id="alice")
        
        service = container.get(OrderService)
        
        print("Calling create_order (success)...")
        service.create_order(user_id="alice", item="book")
        
        print("\nCalling get_order_status...")
        service.get_order_status(order_id="ORD123")

    # --- Simulate Request 2 (causes error) ---
    req_id_2 = f"req-{uuid.uuid4().hex[:4]}"
    print(f"\n--- SIMULATING REQUEST {req_id_2} (User: bob) ---")
    with container.scope("request", req_id_2):
        ctx = container.get(RequestContext)
        ctx.load(request_id=req_id_2, user_id="bob")
        
        service = container.get(OrderService)
        
        print("Calling create_order (failure)...")
        try:
            service.create_order(user_id="bob", item="error")
        except ValueError as e:
            print(f"Caught expected error: {e}")

if __name__ == "__main__":
    run_simulation()
```

### 5\. Example Output (Logs)

```json
{"event": "method_entry", "request_id": "req-...", "user_id": "alice", "class": "OrderService", "method": "create_order"}
{"event": "method_exit", "request_id": "req-...", "user_id": "alice", "class": "OrderService", "method": "create_order", "status": "success", "duration_ms": 50.12}
{"event": "method_entry", "request_id": "req-...", "user_id": "alice", "class": "OrderService", "method": "get_order_status"}
{"event": "method_exit", "request_id": "req-...", "user_id": "alice", "class": "OrderService", "method": "get_order_status", "status": "success", "duration_ms": 20.05}
{"event": "method_entry", "request_id": "req-...", "user_id": "bob", "class": "OrderService", "method": "create_order"}
{"event": "method_exit", "request_id": "req-...", "user_id": "bob", "class": "OrderService", "method": "create_order", "status": "failure", "duration_ms": 50.33, "exception_type": "ValueError", "exception_message": "Invalid item specified"}
```

## Benefits

  * **Automatic Context:** Logs automatically include `request_id` etc., without passing them manually.
  * **Structured Data:** JSON logs are easily parseable by log aggregation systems.
  * **Clean Code:** Service methods focus purely on business logic.
  * **Reusable:** The interceptor can be applied anywhere.

