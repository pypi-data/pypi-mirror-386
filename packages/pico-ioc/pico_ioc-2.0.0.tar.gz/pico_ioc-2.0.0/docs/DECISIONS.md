# DECISIONS.md — pico-ioc

This document records **technical and architectural decisions** for pico-ioc.
Each entry includes a rationale and implications. If a decision is later changed, mark it **[REVOKED]** and link to the replacement.

---

## ✅ Current Decisions (Reflecting v2 Architecture)

### 1) Minimum Python version: **3.10**
**Decision**: Require Python **3.10+**.
**Rationale**: `typing.Annotated` and improved `get_type_hints` are crucial for qualifiers, list injection, and clean internal implementation.
**Implications**: Users must use Python 3.10 or newer. CI/CD targets 3.10+.

---

### 2) Keys: **Typed keys preferred**
**Decision**: Primarily use class/type keys (e.g., `UserService`) for registration and resolution. String keys are supported but discouraged.
**Rationale**: Enhances type safety, IDE support, and reduces potential collisions.
**Implications**: Documentation emphasizes type-based injection. String keys remain for specific cases (e.g., configuration values, legacy integration).

---

### 3) Default Lifecycle: **Singleton per container**
**Decision**: The default scope for components (`@component`) is `singleton`. One instance is created per container and cached.
**Rationale**: Simple, fast, and matches common use cases for services and clients.
**Implications**: Users must explicitly use `@scope("prototype")` or other scope decorators for different lifecycles.

---

### 4) Fail-Fast Bootstrap: **Eager Validation**
**Decision**: Perform **eager validation** of component dependencies during `init()`. Check if a provider exists for every required dependency (excluding `@lazy` components by default).
**Rationale**: Surface wiring errors (missing providers) immediately at startup, enhancing reliability over runtime failures.
**Implications**: Increases startup time slightly. Potential `ProviderNotFoundError` for dependencies only used by `@lazy` components may be deferred until first access. *(See ADR-006)*

---

### 5) Qualifiers & Collection Injection: **First-class via `Annotated`**
**Decision**: Support `Qualifier` tags via `@qualifier(...)` and inject filtered lists using `typing.Annotated[List[Type], Qualifier(...)]`.
**Rationale**: Provides a standard, type-safe mechanism for managing multiple implementations of an interface without custom registries.
**Implications**: Requires Python 3.9+ for `Annotated`. Preserves registration order in injected lists.

---

### 6) Overrides in `init(...)`
**Decision**: Allow replacing components at bootstrap via `init(..., overrides={...})`.
**Rationale**: Simplifies unit testing and mocking without needing complex setup or separate modules.
**Implications**: Overrides are applied *before* any instances are created. Supports overriding with instances, callables (providers), or `(callable, lazy_bool)`.

---

### 7) Conditional Providers: **Profiles, Env Vars, Predicates**
**Decision**: Support conditional registration using `@conditional(profiles=..., require_env=..., predicate=...)`.
**Rationale**: Enables environment-specific configurations (prod vs. test vs. dev), feature flags, and optional integrations declaratively.
**Implications**: Components might not be registered if conditions aren't met, potentially leading to `ProviderNotFoundError` if depended upon. Bootstrap error occurs if a required *eager* dependency is inactive. *(See ADR-006)*

---

### 8) Deterministic Provider Selection: **Prefer `@primary`**
**Decision**: When multiple providers implement the same key (type), select the one marked `@primary`. If ambiguity remains, raise `InvalidBindingError`. `@on_missing` acts as a fallback if no primary or direct provider is found.
**Rationale**: Provides explicit control over default implementations, making wiring predictable. Avoids reliance on implicit scan order.
**Implications**: Developers must use `@primary` (or qualifiers/overrides) to resolve ambiguity between multiple implementations.

---

### 9) Concurrency & Safety: **Immutable Container, Context-Aware Scopes**
**Decision**: The container's configuration (providers, metadata) is **immutable** after `init()`. Caches (`singleton`, `request`, etc.) are isolated and thread/task-safe using appropriate locking or `contextvars`.
**Rationale**: Ensure safe usage in multi-threaded and asynchronous applications without external locking.
**Implications**: Components themselves must be thread/task-safe if used concurrently across scopes. `contextvars` require proper context propagation in complex threading/async scenarios.

---

### 10) Configuration: **Dual System (`@configuration` and `@configured`)**
**Decision**: Support two configuration injection mechanisms:
    1. **`@configuration`**: For simple, flat key-value settings populated from ordered `ConfigSource`s (`EnvSource`, `FileSource`).
    2. **`@configured`**: For complex, nested configuration trees populated from ordered `TreeSource`s (`YamlTreeSource`, `JsonTreeSource`), mapping directly to `dataclass` graphs.
**Rationale**: `@configuration` handles simple cases easily. `@configured` provides a powerful, type-safe solution for modern, structured configuration practices, inspired by frameworks like Spring Boot.
**Implications**: Developers choose the system appropriate for their needs. `@configured` is generally recommended for new, complex applications. *(See ADR-002)*

---

### 11) AOP: **Explicit Proxy via `@intercepted_by`**
**Decision**: Implement AOP using **method interception** via a dynamic **`UnifiedComponentProxy`**. Interceptors are defined using the `MethodInterceptor` protocol and applied explicitly with `@intercepted_by(...)`. Rejected alternatives involving metaclass programming or bytecode manipulation.
**Rationale**: Provides powerful AOP capabilities using standard Python features (decorators, proxies). Explicit application (`@intercepted_by`) is clearer and more controllable than global or rule-based interception. Avoids the complexity and potential fragility of metaprogramming/bytecode.
**Implications**: Adds a proxy layer (minor performance overhead, potential debug complexity). Developers must explicitly decorate methods to apply aspects. *(See ADR-005)*

---

### 12) Async Support: **Native Integration**
**Decision**: Integrate `asyncio` support deeply throughout the container. Provide `container.aget()`, support `async def` providers, `__ainit__`, async lifecycle hooks (`@configure`, `@cleanup`), async AOP, and an async Event Bus.
**Rationale**: Essential for modern I/O-bound Python applications. Avoids blocking the event loop during component resolution or lifecycle management.
**Implications**: Dual API (`get`/`aget`). Developers must use `aget` and `cleanup_all_async` in async contexts. *(See ADR-001)*

---

### 13) Context-Aware Scopes: **`contextvars`-Based**
**Decision**: Implement dynamic scopes (`request`, `session`, custom) using `contextvars`. Provide `ScopeProtocol`, `ContextVarScope`, `ScopeManager`, `ScopedCaches` (with LRU), and `with container.scope(...)`.
**Rationale**: `contextvars` provide a robust mechanism for managing context-local state in both threaded and async environments. Enables per-request or other contextual lifecycles.
**Implications**: Requires explicit scope management (e.g., via middleware) using `container.scope()` or `activate/deactivate`. Potential complexity with context propagation in advanced scenarios. *(See ADR-003)*

---

### 14) Observability: **Built-in Features**
**Decision**: Include features for monitoring and debugging: `container_id`, `container context` (`as_current`), `container.stats()`, `ContainerObserver` protocol, and `container.export_graph()`.
**Rationale**: Essential for understanding and managing complex applications, especially multi-container setups. Makes the container less of a "black box".
**Implications**: Slight overhead for context tracking. `ContainerObserver` and `export_graph` are optional features. *(See ADR-004)*

---

### 15) Event Bus: **Integrated Async Pub/Sub**
**Decision**: Provide a built-in, asynchronous `EventBus` component with `@subscribe` decorator and `AutoSubscriberMixin`.
**Rationale**: Facilitates decoupled, event-driven architectures directly within the container ecosystem. Provides a standard mechanism over ad-hoc solutions.
**Implications**: Adds functionality beyond core DI. Requires registering the `pico_ioc.event_bus` module. Bus is in-process, not a distributed queue replacement. *(See ADR-007)*

---

## ❌ Won’t-Do Decisions (Confirmed for v2)

### A) Alternative scopes (request/session) beyond `contextvars`
**Decision**: Stick to `contextvars` for built-in dynamic scopes. Do not add framework-specific scope implementations (e.g., Flask `g`, Django `request`) directly into the core library.
**Rationale**: Keep `pico-ioc` framework-agnostic. `contextvars` provide a universal mechanism. Framework integrations can bridge framework contexts to `pico-ioc` scopes if needed.
**Implications**: Integration recipes (like for Flask/FastAPI) show how to manage `contextvars`-based scopes using middleware or request hooks.

### B) Hot reload / dynamic re-scan
**Decision**: The container configuration remains **immutable** after `init()`. No built-in support for watching files and automatically reloading the container.
**Rationale**: Conflicts with fail-fast validation and immutability principles. Adds significant complexity and potential for inconsistent states. Hot-reload is better handled by development server tools (like `uvicorn --reload` or the `watchdog` pattern shown in the cookbook).
**Implications**: Developers use external tools or patterns (like the cookbook example) for development-time hot-reloading.

---

## 🗃️ Deprecated / Revoked

* **[REVOKED] Decision #11 (Old)**: Infrastructure-based Interceptor API via `@infrastructure`.
    * **Reason:** Replaced by the simpler, more explicit `@intercepted_by` AOP mechanism using `UnifiedComponentProxy` (ADR-005). The `@infrastructure` role might be repurposed or removed in future versions.

---

## 📜 Changelog of Decisions (v2 Focus)

* **v2.0**: Minimum Python **3.10** adopted.
* **v2.0**: **Native Async Support** added (`aget`, `__ainit__`, async hooks/AOP/EventBus - ADR-001).
* **v2.0**: **Tree-Based Configuration Binding** added (`@configured`, `TreeSource`, `ConfigResolver`, `ObjectGraphBuilder` - ADR-002).
* **v2.0**: **Context-Aware Scopes** implemented (`@scope("request")`, `contextvars`, `container.scope()` - ADR-003).
* **v2.0**: **Observability Features** added (`container_id`, `as_current`, `stats`, `ContainerObserver`, `export_graph` - ADR-004).
* **v2.0**: **AOP Implementation** finalized using `@intercepted_by` and `UnifiedComponentProxy` (ADR-005). Explicit decision against metaprogramming. Old `@infrastructure`-based interceptor plan revoked.
* **v2.0**: **Eager Startup Validation** confirmed as core principle (ADR-006).
* **v2.0**: **Built-in Async Event Bus** added (ADR-007).
* **v2.0**: **`@primary`** confirmed as the primary mechanism for resolving ambiguity (Decision #8 refined).
* **v2.0**: **Configuration Injection** clarified as a dual system (`@configuration` + `@configured`) (Decision #10 updated).

---

**Summary**: `pico-ioc` v2 prioritizes **robustness, async-native operation, powerful configuration, observability, and explicit AOP** using standard Python features. It remains deterministic and aims to fail fast at startup.
```

How does this look? It incorporates the key decisions from the ADRs and clarifies the v2 architecture.
