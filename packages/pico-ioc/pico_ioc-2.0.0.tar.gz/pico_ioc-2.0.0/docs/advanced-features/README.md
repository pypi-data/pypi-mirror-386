# Advanced Features

Welcome to the Advanced Features guide. In the [User Guide](./user-guide/README.md), you mastered the core concepts: registering components, injecting configuration, managing lifecycles, and writing tests. You now have a solid foundation.

This section covers the powerful, enterprise-grade features that `pico-ioc` provides for building truly complex, modern, and resilient applications. These are the tools you'll reach for when you need to solve non-trivial architectural problems.

---

## In This Section

### [1. Async Resolution: `aget`, `__ainit__`](./async-resolution.md)

**Problem:** Your application is built around `asyncio`. Your components need to perform `await` operations during their creation (e.g., `await database.connect()`), and you need to resolve them without blocking the event loop.

**Solution:** `pico-ioc` is **async-native**. This guide covers:
* `container.aget()`: The asynchronous equivalent of `get()`.
* `async def __init__` (via `__ainit__`): How to define asynchronous constructors.
* `async def @provides`: Creating components from asynchronous factory methods.
* `async def @cleanup`: Asynchronously releasing resources.

---

### [2. AOP & Interceptors: `@intercepted_by`](./aop-interceptors.md)

**Problem:** You have cross-cutting concerns that pollute your business logic. You need to add logging, performance tracing, caching, or transaction management to dozens of methods, but you don't want to copy-paste that code everywhere.

**Solution:** `pico-ioc` provides **Aspect-Oriented Programming (AOP)**. You'll learn how to create a `MethodInterceptor` (a single class that wraps your method) and apply it non-intrusively with the `@intercepted_by` decorator. This lets you separate *business* logic from *technical* logic.

---

### [3. The Event Bus: `EventBus`, `subscribe`](./event-bus.md)

**Problem:** Your services are too tightly coupled. When a `UserService` creates a user, it also needs to call the `EmailService`, the `AnalyticsService`, and the `AuditService`. This creates a rigid and brittle architecture.

**Solution:** `pico-ioc` includes a **built-in asynchronous event bus**. You'll learn how to decouple your services by having `UserService` simply `publish(UserCreatedEvent(...))`. Other services can `subscribe` to that event and react independently, without `UserService` even knowing they exist.

---

### [4. Conditional Binding: `@primary`, `@on_missing`, `@conditional`](./conditional-binding.md)

**Problem:** You need fine-grained control over *which* components are registered.
* How do you define a "default" implementation when multiple exist?
* How do you provide a "fallback" component if no other is available?
* How do you *disable* a component unless a specific environment variable is set?

**Solution:** This guide covers the advanced decorators that control component registration:
* `@primary`: Marks the "default" implementation to inject.
* `@on_missing`: Registers a component *only if* no other component satisfies the dependency.
* `@conditional`: The most powerful option. Register a component based on active profiles, environment variables, or a custom predicate function.

---

### [5. Health Checks: `@health`](./health-checks.md)

**Problem:** Your application runs in a container (like Kubernetes) and you need to expose a `/health` endpoint. This endpoint must check that all critical infrastructure (like the database and external APIs) are reachable.

**Solution:** `pico-ioc` provides a built-in health check system. You'll learn how to use the `@health` decorator to tag methods as health checks. The container can then call `container.health_check()` to run *all* registered checks and give you a simple dictionary report of what's up and what's down.

---

## Next Steps

Let's dive into the most important advanced feature for modern Python:

* **[Async Resolution (`aget`, `__ainit__`)](./async-resolution.md)**: Learn how to build and resolve components asynchronously.

