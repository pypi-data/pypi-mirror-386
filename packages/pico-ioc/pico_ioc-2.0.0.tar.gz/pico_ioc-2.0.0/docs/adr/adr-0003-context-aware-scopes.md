## ADR-003: Context-Aware Scopes

**Status:** Accepted

### Context

Many applications, especially web services, require components whose lifecycle is tied to a specific context (e.g., an HTTP request or a user session). The default `singleton` and `prototype` scopes are insufficient for managing state within these contexts. We needed a mechanism for "scoped singletons" (one instance per active context).

### Decision

We introduced **context-aware scopes** based on Python's `contextvars`:

1.  **`ScopeProtocol`:** Defined a minimal interface for scope implementations, requiring only `get_id() -> Any | None`.
2.  **`ContextVarScope`:** Provided a standard implementation of `ScopeProtocol` wrapping a `contextvars.ContextVar`. This implementation also includes `activate(id)` and `deactivate(token)` methods.
3.  **`ScopeManager`:** An internal registry holding `ScopeProtocol` implementations for named scopes (e.g., `"request"`, `"session"`). It provides methods like `activate`, `deactivate`, and `get_id`.
4.  **`@scope("scope_name")` Decorator:** Allows components to be assigned to a specific scope.
5.  **`ScopedCaches`:** Modified to handle caches keyed by `(scope_name, scope_id)`, using an LRU mechanism to evict caches for inactive scope IDs.
6.  **Container API:** Added `container.activate_scope(name, id)`, `deactivate_scope(name, token)`, and the `with container.scope(name, id):` context manager for easy scope management. Default scopes like `"request"`, `"session"`, and `"transaction"` are pre-registered.

### Consequences

**Positive:** 👍
* Enables safe management of context-specific state (e.g., per-request data).
* Integrates naturally with `asyncio` due to `contextvars`.
* Provides a clean API for activating/deactivating scopes (especially the `with container.scope():` manager).
* Extensible: users can define and register custom scopes via `init(custom_scopes=...)`.

**Negative:** 👎
* Relies on `contextvars`, which can have subtle behavior if not used carefully (especially across thread boundaries without proper context propagation).
* Requires explicit scope activation/deactivation in the application's entry point (e.g., web middleware). `pico-ioc` does not automatically manage scope lifecycles.
* Can increase memory usage if many scope instances are kept active simultaneously (though `ScopedCaches` LRU mitigates this).

