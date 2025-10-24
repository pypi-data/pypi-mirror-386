# Architecture

Welcome to the Architecture section.

The previous sections (User Guide, Advanced Features, Integrations, Cookbook) focused on the **"What"**—*what* you can do with `pico-ioc`.

This section focuses on the **"Why"** and the **"How"**—*why* `pico-ioc` was designed the way it is, and *how* it works internally.

This content is intended for:
* **Contributors:** Anyone who wants to contribute to the `pico-ioc` codebase.
* **Architects:** Users who need to understand the framework's performance, trade-offs, and core mechanics at the deepest level.
* **Curious Developers:** Anyone who enjoys learning how their tools work "under the hood."

Here, we will move past the public API and explore the core components that make the container function, from the `Registrar` and `ComponentLocator` to the `UnifiedComponentProxy` that powers AOP.

---

## In This Section

### [1. Design Principles](./design-principles.md)

The "Why." This document explains the core philosophies that guided `pico-ioc`'s development. Understanding these principles will help you understand *why* certain features exist and others do not.
* **Fail-Fast at Startup:** The importance of eager validation.
* **Observability-First:** Why `container_id` and `observers` are core features.
* **Async-Native:** Designing for `asyncio` from the ground up.
* **Separation of Concerns:** The philosophy behind AOP and the Event Bus.

### [2. Comparison to Other Libraries](./comparison.md)

This document (currently in `docs/architecture/comparison.md` as per your `next.md`) provides a feature-by-feature and philosophical comparison against other popular Python DI libraries (like `dependency-injector`, `punq`) and framework-native DI (like FastAPI's `Depends`). It highlights `pico-ioc`'s unique value proposition.

### [3. Internals Deep-Dive](./internals.md)

The "How." This is a deep dive into the internal mechanics of the container. You'll learn about:
* The **Initialization Flow** (`Registrar`, `select_and_bind`).
* The **Resolution Algorithm** (`_resolve_chain`, `_cache_for`).
* The **AOP Proxy** (`UnifiedComponentProxy`, `__getattr__`).
* The **Configuration Binders** (`ConfigResolver`, `ObjectGraphBuilder`).

---

## Next Steps

Let's begin with the "Why."

* **[Design Principles](./design-principles.md)**: Understand the core philosophy behind `pico-ioc`.

