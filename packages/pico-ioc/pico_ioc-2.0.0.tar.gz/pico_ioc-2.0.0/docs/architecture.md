# Pico IOC: Internal Architecture

This document describes the internal design and mechanics of the Pico IOC framework.

## 1. System Architecture

### 1.1. Core Components

```text
┌─────────────────────────────────────────────────────┐
│              PicoContainer (Facade)                 │
├─────────────────────────────────────────────────────┤
│  ComponentFactory  │  ScopedCaches  │  ScopeManager │
├─────────────────────────────────────────────────────┤
│         ComponentLocator  │  Registrar              │
├─────────────────────────────────────────────────────┤
│              UnifiedComponentProxy (AOP)            │
└─────────────────────────────────────────────────────┘
````

  * **PicoContainer**: The public API and facade for the container. It orchestrates `get`/`aget` calls, manages scope contexts, and holds references to the other components.
  * **Registrar**: A short-lived object used during `init()`. It scans modules, discovers components, resolves bindings, runs validation, and populates the `ComponentFactory`.
  * **ComponentFactory**: Stores the final "recipe" (a `Provider` callable) for creating each component.
  * **ScopedCaches**: Manages the lifecycles and storage of component instances (singleton, request, etc.).
  * **ScopeManager**: Manages the active ID for `ContextVar`-based scopes.
  * **ComponentLocator**: An queryable index of all component metadata.
  * **UnifiedComponentProxy**: The dynamic proxy used for AOP and `@lazy`.

### 1.2. Initialization Flow (via `init()`)

1.  **Scan**: `_iter_input_modules` walks packages to find modules.
2.  **Register**: `Registrar.register_module` inspects module members for decorators (`@component`, `@factory`, etc.).
3.  **Queue**: Candidates are queued in `Registrar._candidates`. Conditional logic (`@conditional`) is evaluated here.
4.  **Select**: `Registrar.select_and_bind` picks the best provider for each key (respecting `@primary`) and binds it in the `ComponentFactory`.
5.  **Promote Scopes**: `_promote_scopes` runs to prevent scope leaks (see below).
6.  **Apply Fallbacks**: `on_missing` components are registered if their target is still missing.
7.  **Validate**: `_validate_bindings` inspects all component dependencies. If a dependency cannot be resolved, `InvalidBindingError` is raised.
8.  **Finalize**: `PicoContainer` is created and the `ComponentLocator` and `Registrar` are attached.

-----

## 2\. Dependency Resolution

### 2.1. Resolution Algorithm

Resolution is handled by `PicoContainer.get(key)` and `aget(key)`.

1.  **Check Cache**: The container checks the appropriate cache (e.g., `_singleton` or a `request` cache) for an existing instance.
2.  **Check Cycle**: The requested `key` is checked against the `_resolve_chain` (a `ContextVar`). If present, `CircularDependencyError` is raised.
3.  **Push to Stack**: The `key` is added to the `_resolve_chain`.
4.  **Get Provider**: The `ComponentFactory` provides the `Provider` (a callable) for the `key`.
5.  **Create Instance**:
      * The `Provider` is called. This triggers `_resolve_args` to find dependencies for the component's `__init__` or factory method.
      * This is a recursive process: `_resolve_args` calls `pico.get()` for each dependency, starting the flow over at step 1.
      * For `aget`, if the provider is a coroutine, it is `await`ed.
6.  **Wrap Proxy**: The new instance is passed to `_maybe_wrap_with_aspects` to wrap it in a `UnifiedComponentProxy` if it has AOP interceptors.
7.  **Put in Cache**: The (possibly proxied) instance is stored in the cache.
8.  **Pop from Stack**: The `key` is removed from `_resolve_chain`.
9.  **Return Instance**.

### 2.2. Startup Validation

The `Registrar._validate_bindings` method performs "eager" validation at startup. It iterates all registered component metadata and inspects their constructor/factory dependencies. For each dependency type, it queries the internal metadata to ensure a provider *exists*, preventing runtime `ProviderNotFoundError` errors.

-----

## 3\. Scope Management Internals

### 3.1. ScopeManager

The `ScopeManager` is a simple registry for `ScopeProtocol` implementations. For dynamic scopes (`request`, `session`), it uses `ContextVarScope`, which wraps a `contextvars.ContextVar`. `activate()` sets the variable, and `get_id()` reads it, allowing component resolution to be context-aware.

### 3.2. ScopedCaches

This class holds the actual component instances.

  * `_singleton`: A single `ComponentContainer` (a dict).
  * `_by_scope`: A `dict` mapping scope names (e.g., "request") to an `OrderedDict`.
  * The `OrderedDict` maps a *scope ID* (e.g., "req-123") to a `ComponentContainer` for that specific ID. It's used as an LRU cache to evict old, inactive scope instances.

-----

## 4\. AOP Internals

### 4.1. UnifiedComponentProxy

This class is the heart of AOP and `@lazy`.

  * **Lazy**: If created for a `@lazy` component, `_target` is `None` and `_creator` is the component's provider. The `_get_real_object()` method is called on the *first* attribute access, which then executes the creator and saves the result to `_target`.
  * **AOP**: If created for AOP, `_target` is set immediately to the real instance.
  * **`__getattr__`**: This is the magic method.
    1.  It retrieves the real attribute from the target.
    2.  If the attribute isn't callable (e.g., a property), it's returned directly.
    3.  If it *is* callable, it checks for `_pico_interceptors_`.
    4.  If interceptors exist, it builds a chain of responsibility using `dispatch_method` and returns a new wrapped function that executes the chain.
  * **Serialization**: `__reduce_ex__` is implemented to ensure that `pickle` serializes the *real object* (`_target`), not the proxy, allowing proxied objects to be sent across processes.

-----

## 5\. ComponentLocator and Indexing

The `ComponentLocator` is an introspection tool built from the `Registrar`'s final metadata. It maintains several inverted indexes (as `dict`s) to allow for fast querying based on metadata:

  * `"qualifier"`: `Qualifier` $\rightarrow$ `List[KeyT]`
  * `"primary"`: `bool` $\rightarrow$ `List[KeyT]`
  * `"infra"`: `str` $\rightarrow$ `List[KeyT]` (e.g., "component", "factory")

The fluent API (`.with_qualifier_any()`, etc.) simply performs set intersections on these pre-built lists.

-----

## 6\. Advanced Internal Mechanisms

### 6.1. Automatic Scope Promotion

The `Registrar._promote_scopes` method prevents scope leaks (e.g., a `singleton` depending on a `request`-scoped object). It iterates all `singleton` components and inspects their dependencies. If a singleton depends on a component with a narrower scope (e.g., `request`), the singleton's *own* scope is automatically "promoted" to `request`.

### 6.2. Event Bus

The `EventBusInfra` is registered as a component and injected. It maintains a dictionary mapping `Event` types to a sorted list of `_Subscriber` callables. The `publish` method iterates this list, handling `async` and sync subscribers and applying `ExecPolicy` (e.g., running sync subscribers in a `ThreadPool`).

-----

## 7\. Design Patterns

  * **Inversion of Control (IoC)**: Container manages the lifecycle.
  * **Dependency Injection (DI)**: Constructor/method injection.
  * **Service Locator**: `ComponentLocator` with queries.
  * **Proxy Pattern**: `UnifiedComponentProxy` for lazy + AOP.
  * **Chain of Responsibility**: Interceptor chain (`dispatch_method`).
  * **Factory Pattern**: `@factory` and `@provides`.
  * **Strategy Pattern**: Multiple implementations (`Database`) with `@primary`.
  * **Observer Pattern**: `ContainerObserver` for monitoring.
  * **Publisher/Subscriber**: `EventBusInfra`.

-----

## 8\. Critical Analysis

### 8.1. Strengths

  * **Startup Validation**: `InvalidBindingError` prevents runtime failures.
  * **Cycle Detection**: `CircularDependencyError` provides clear, actionable error messages.
  * **Async-Native**: Full `async`/`await` support in `aget` and AOP is a significant advantage.
  * **Testability**: Overrides and profiles are first-class concepts.

### 8.2. Weaknesses

  * **Performance**: The heavy use of `inspect.signature` and reflection in `_resolve_args` on every non-cached resolution can be a bottleneck.
  * **"Magic"**: The proxying (`UnifiedComponentProxy`) and `ContextVar`-based scoping can be difficult to debug for users unfamiliar with these concepts.

-----

## 9\. Improvement Recommendations

  * **High Priority**: Implement caching for reflection results (like `inspect.signature`) to reduce overhead on resolution.
  * **Medium Priority**: Implement the logic for the `@eager` decorator to force-load specific singletons at startup.
  * **Medium Priority**: Integrate with OpenTelemetry to automatically create spans for component resolutions and AOP-intercepted methods.
  * **Low Priority**: Expose the `ComponentLocator` via a query API (e.g., GraphQL-like) for runtime introspection.

