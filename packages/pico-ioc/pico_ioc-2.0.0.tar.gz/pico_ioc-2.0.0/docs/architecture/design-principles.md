# Design Principles

Understanding *why* `pico-ioc` is built the way it is can help you use it more effectively and anticipate its behavior. This framework wasn't created in a vacuum; it's the result of specific design choices aimed at solving common problems in large-scale Python application development.

These are the core principles that guided its architecture:

---

## 1. Fail-Fast at Startup ⚡

**Principle:** It's better to detect configuration and wiring errors *immediately* when the application starts (`init()`) than to encounter them *later* at runtime during a user request.

**Rationale:** Runtime errors caused by missing dependencies (`ProviderNotFoundError`) or invalid configuration are frustrating to debug and can lead to unpredictable application behavior. In production, a runtime failure might only occur under specific load or after a certain code path is hit, making it hard to reproduce.

**Implementation:**
* **Eager Validation:** The `Registrar._validate_bindings` step during `init()` proactively checks if a provider exists for every required dependency in your components' constructors and factory methods. If a dependency cannot be satisfied, `init()` raises an `InvalidBindingError` immediately, preventing the application from starting in an invalid state.
* **Clear Cycle Detection:** `CircularDependencyError` provides the full dependency chain, making it easy to identify and fix cycles during development.

**Trade-off:** This eager validation adds a small overhead to application startup time. However, this is generally negligible compared to the cost of debugging runtime failures. (`@lazy` provides an escape hatch for specific components where startup cost is critical).

---

## 2. Observability First 🔭

**Principle:** In complex or distributed systems, understanding *what* the container is doing, *when*, and *why* is crucial for debugging and monitoring. Observability shouldn't be an afterthought; it should be built into the core.

**Rationale:** As applications grow, tracking component lifecycles, identifying performance bottlenecks in resolution, or managing multiple container instances (e.g., multi-tenant) becomes challenging without proper introspection tools.

**Implementation:**
* **Container Context:** Every container has a unique `container_id`. The `with container.as_current()` mechanism ensures that logs, metrics, and traces can always be correlated to a specific container instance, even in multi-tenant or hot-reloading scenarios.
* **Built-in Stats:** `container.stats()` provides essential KPIs (cache hits, resolve counts) out-of-the-box.
* **Observer Protocol:** `ContainerObserver` offers a low-level hook for integrating with sophisticated tracing systems (like OpenTelemetry) by providing events like `on_resolve` and `on_cache_hit`.
* **Graph Export:** `container.export_graph()` allows developers to visualize the entire dependency structure, aiding in debugging and architectural understanding.

---

## 3. Async Native  asyncio 🔄

**Principle:** Asynchronous programming using `asyncio` is the standard for I/O-bound applications in modern Python. A DI container should fully embrace `async`/`await` without workarounds or blocking the event loop.

**Rationale:** Many components need to perform asynchronous operations during initialization (e.g., connecting to a database) or cleanup. A synchronous DI container forces awkward patterns or risks blocking the event loop when resolving async components.

**Implementation:**
* **`aget()`:** A dedicated asynchronous resolution method (`container.aget()`).
* **Async Lifecycle:** Support for `async def` in factory `@provides` methods, the `__ainit__` initializer, and `@cleanup` hooks.
* **Async AOP:** `MethodInterceptor`s can be `async def` and correctly `await` the original async method.
* **Async Event Bus:** The built-in `EventBus` is fully asynchronous.

---

## 4. Explicit Configuration over Convention ✨

**Principle:** While conventions can be helpful, critical configuration and wiring should be explicit and discoverable through decorators and type hints, rather than relying on implicit naming rules or complex classpath scanning.

**Rationale:** Implicit conventions can make application behavior hard to understand and debug. Explicit decorators (`@component`, `@qualifier`, `@configured`) make the container's behavior clear and allow static analysis tools (like type checkers) to reason about the code.

**Implementation:**
* **Decorator-Driven:** Registration relies on explicit decorators.
* **Type Hint Injection:** Dependencies are resolved based on constructor/method type hints.
* **Explicit Configuration:** `@configuration` and `@configured` require explicit mapping between configuration sources (files, env vars) and target `dataclasses`.

---

## 5. Separation of Concerns (SoC) 🧩

**Principle:** Promote loose coupling and high cohesion by providing tools that help separate different kinds of logic (business, technical, configuration).

**Rationale:** Tightly coupled code is hard to test, maintain, and evolve. Mixing technical concerns (like logging, transaction management) with business logic makes both harder to understand.

**Implementation:**
* **Dependency Injection:** The core pattern decouples components.
* **AOP (`@intercepted_by`)**: Explicitly designed to extract cross-cutting concerns (logging, caching, security) into reusable `MethodInterceptor`s.
* **Event Bus:** Decouples components by allowing them to communicate asynchronously via events instead of direct calls.
* **Configuration Binding:** Separates configuration loading and parsing from the components that use the configuration values.

---

## Next Steps

Now that you understand the "Why," let's compare `pico-ioc` to other libraries to see how these principles translate into unique features.

* **[Comparison to Other Libraries](./comparison.md)**: See how `pico-ioc` stacks up against alternatives.

