# Welcome to pico-ioc

`pico-ioc` is a powerful, async-native, and observability-first Inversion of Control (IoC) container for Python. It's designed to bring the power of enterprise-grade dependency injection, configuration binding, and AOP (Aspect-Oriented Programming) from frameworks like Spring into the modern Python ecosystem.

This documentation site guides you from your first component to building complex, observable, and testable applications.

## Key Features

* 🚀 **Async-Native:** Full support for `async`/`await` in component resolution (`aget`), lifecycle methods (`__ainit__`, `@cleanup`), AOP interceptors, and the Event Bus.
* 🌳 **Advanced Tree-Binding:** Use `@configured` to map complex YAML/JSON configuration trees directly to `dataclass` graphs, including support for `Union` types and custom discriminators.
* 🔬 **Observability-First:** Built-in container contexts (`as_current`), stats (`.stats()`), and observer protocols (`ContainerObserver`) to monitor, trace, and debug your application's components.
* ✨ **Powerful AOP:** Intercept method calls for cross-cutting concerns (like logging, tracing, or caching) using `@intercepted_by` without modifying your business logic.
* ✅ **Fail-Fast Validation:** The container validates all component dependencies at startup (`init()`), preventing `ProviderNotFoundError` exceptions at runtime.
* 🧩 **Rich Lifecycle:** Full control over component lifecycles with `@scope`, `@lazy` instantiation, `@configure` setup methods, and `@cleanup` teardown hooks.

## Documentation Structure

### 1. Getting Started

Start here for a 5-minute tutorial to get `pico-ioc` running.

* [Overview](./getting-started/README.md)
* [Installation](./getting-started/installation.md)
* [5-Minute Quick Start](./getting-started/quick-start.md)

### 2. User Guide

The main guide covering the 80% of features you'll use daily.

* [Overview](./user-guide/README.md)
* [Core Concepts (`@component`, `@factory`)](./user-guide/core-concepts.md)
* [Basic Configuration (`@configuration`)](./user-guide/configuration-basic.md)
* [Configuration Tree Binding (`@configured`)](./user-guide/configuration-binding.md)
* [Scopes, Lifecycle & `@lazy`](./user-guide/scopes-lifecycle.md)
* [Qualifiers & List Injection](./user-guide/qualifiers-lists.md)
* [Testing Applications](./user-guide/testing.md)

### 3. Advanced Features

Powerful features for complex application architectures.

* [Overview](./advanced-features/README.md)
* [Async Resolution (`aget`, `__ainit__`)](./advanced-features/async-resolution.md)
* [AOP & Interceptors](./advanced-features/aop-interceptors.md)
* [The Event Bus](./advanced-features/event-bus.md)
* [Conditional Binding (`@conditional`, `@primary`)](./advanced-features/conditional-binding.md)
* [Health Checks (`@health`)](./advanced-features/health-checks.md)

### 4. Observability

Monitor, trace, and debug your application's components.

* [Overview](./observability/README.md)
* [Container Context (`as_current`)](./observability/container-context.md)
* [Observers & Metrics (`stats`)](./observability/observers-metrics.md)
* [Exporting the Dependency Graph](./observability/exporting-graph.md)

### 5. Integrations

Recipes for using `pico-ioc` with popular frameworks.

* [Overview](./integrations/README.md)
* [FastAPI](./integrations/web-fastapi.md)
* [Flask](./integrations/web-flask.md)
* [Django](./integrations/web-django.md)
* [AI & LangChain](./integrations/ai-langchain.md)

### 6. Cookbook (Patterns)

Complete, copy-paste examples of common architectural patterns.

* [Overview](./cookbook/README.md)
* [Pattern: Multi-Tenant Applications](./cookbook/pattern-multi-tenant.md)
* [Pattern: Hot Reload (Dev Server)](./cookbook/pattern-hot-reload.md)
* [Pattern: CLI Applications](./cookbook/pattern-cli-app.md)

### 7. Architecture

The "Why" and "How" behind `pico-ioc`'s design.

* [Overview](./architecture/README.md)
* [Design Principles](./architecture/design-principles.md)
* [Comparison to Other Libraries](./architecture/comparison.md)
* [Internals Deep-Dive](./architecture/internals.md)

### 8. API Reference

A "cheatsheet" for all public APIs.

* [Overview](./api-reference/README.md)
* [Glossary](./api-reference/glossary.md)
* [Decorators Reference](./api-reference/decorators.md)
* [`PicoContainer` API](./api-reference/container.md)
* [Protocols (`MethodInterceptor`, etc.)](./api-reference/protocols.md)
```

