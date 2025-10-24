# Observability

Welcome to the Observability section.

In a simple application, you have one container, and it's easy to know what's happening. In a complex, production-grade application, you might have:
* Multiple, isolated containers running in the same process (e.g., for multi-tenant applications).
* Dynamic container reloading (e.g., in a development server).
* Complex dependency graphs that are hard to visualize.
* A need to trace component resolution or measure performance.

`pico-ioc` was built with these challenges in mind. It is **observability-first**, meaning it provides the tools you need to monitor, trace, and debug the container's behavior at runtime.

This section covers the tools that give you a "window" into the container's internal state.

---

## In This Section

### [1. Container Context: `as_current`](./container-context.md)

**Problem:** You have multiple containers and need a way to manage which one is "active" for the current thread or `asyncio` task. This is the foundation for all multi-tenant or multi-container patterns.

**Solution:** This guide covers the container context system. You'll learn:
* `container.container_id`: How every container gets a unique ID for tracing.
* `with container.as_current()`: The context manager that activates a container.
* `PicoContainer.get_current()`: How to access the currently-active container from anywhere.
* `container.shutdown()`: The proper way to shut down a container and remove it from the global registry.

---

### [2. Observers & Metrics: `stats`](./observers-metrics.md)

**Problem:** You need to monitor the container's performance. How many components has it resolved? What is the cache hit rate? You also want to integrate with custom tracing tools like OpenTelemetry.

**Solution:** This guide explains the built-in metrics and extension points. You'll learn:
* `container.stats()`: How to get a dictionary of built-in metrics (uptime, resolve count, cache hits, etc.).
* `ContainerObserver`: A protocol you can implement to create a custom "listener" that receives events for component resolutions, allowing you to create custom metrics or OpenTelemetry spans.

---

### [3. Exporting the Dependency Graph](./exporting-graph.md)

**Problem:** Your application has hundreds of components. You're getting a `CircularDependencyError` or just can't figure out *why* a component is being injected. You need to *see* the dependency graph.

**Solution:** `pico-ioc` can export its entire dependency graph to a `.dot` file. This guide shows you how to use `container.export_graph()` and then use tools like Graphviz to generate a visual diagram of your entire application architecture.

---

## Next Steps

Let's start with the most fundamental concept of observability: the container context.

* **[Container Context (`as_current`)](./container-context.md)**: Learn how to manage the active container.

