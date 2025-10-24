# API Reference

Welcome to the `pico-ioc` API Reference.

This section provides a concise summary of all public APIs, including decorators, the `PicoContainer` class, and key protocols. It's designed for quick lookups when you know what you're looking for but need to check specific parameters or method signatures.

Unlike the User Guide, this section is purely descriptive and does not provide detailed explanations or usage examples. For learning how to *use* these APIs, please refer to the [User Guide](../user-guide/README.md) and [Advanced Features](../advanced-features/README.md) sections.

---

## In This Section

* **[Glossary](./glossary.md)**
    * A quick definition of key terms used throughout `pico-ioc` (e.g., Component, Provider, Scope, Qualifier).

* **[Decorators Reference](./decorators.md)**
    * A list of all decorators (e.g., `@component`, `@factory`, `@provides`, `@configured`, `@intercepted_by`, `@health`) and their available parameters.

* **[`PicoContainer` API](./container.md)**
    * A reference for the main `PicoContainer` class, listing its public methods (`init`, `get`, `aget`, `stats`, `shutdown`, `as_current`, `export_graph`, etc.) and their signatures.

* **[Protocols](./protocols.md)**
    * Details the interfaces for extending `pico-ioc`:
        * `MethodInterceptor`: For implementing AOP.
        * `ContainerObserver`: For monitoring container events.
        * `ScopeProtocol`: For defining custom scopes.
        * `ConfigSource` / `TreeSource`: For providing configuration values.

---

## Next Steps

Start with the glossary to ensure a common understanding of terms.

* **[Glossary](./glossary.md)**: Definitions of core `pico-ioc` concepts.

