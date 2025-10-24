# Comparison to Other Libraries

Choosing a dependency injection (DI) framework, or deciding whether to use one at all, involves trade-offs. `pico-ioc` makes specific design choices (as outlined in [Design Principles](./design-principles.md)) that differentiate it from other popular solutions in the Python ecosystem.

This comparison aims to help you understand where `pico-ioc` fits best and why you might choose it over alternatives like `dependency-injector`, `punq`, or the built-in DI systems of web frameworks like FastAPI.

---

## Feature Comparison Matrix

| Feature                      | pico-ioc          | dependency-injector | punq             | FastAPI `Depends` |
| :--------------------------- | :---------------: | :-----------------: | :--------------: | :---------------: |
| **Primary Style** | Decorators + TH   | Declarative YAML/Py | Decorators + TH  | Function Wrappers |
| **Type Hint Based** | ✅ Yes            | ⚠️ Partial¹        | ✅ Yes           | ✅ Yes            |
| **Startup Validation** | ✅ Yes (Eager)    | ❌ No (Runtime)   | ❌ No (Runtime)  | ❌ No (Runtime)   |
| **Circular Dep. Error** | ✅ Full Chain     | ✅ Basic          | ✅ Basic         | ✅ Basic          |
| **Async Support** | ✅ Native (`aget`) | ⚠️ Partial²       | ❌ No            | ✅ Native         |
| **AOP (Interceptors)** | ✅ Built-in       | ❌ No             | ❌ No            | ❌ No             |
| **Scopes (Singleton)** | ✅ Yes            | ✅ Yes            | ✅ Yes           | ✅ Yes³           |
| **Scopes (Prototype)** | ✅ Yes            | ✅ Yes            | ✅ Yes           | ⚠️ Via `use_cache=False` |
| **Scopes (Web/ContextVar)** | ✅ Built-in       | ✅ Built-in       | ❌ No            | ✅ Native (Request)|
| **Configuration Binding** | ✅ Tree + Basic   | ✅ Basic (KV)     | ❌ Manual        | ❌ Manual         |
| **Qualifiers/Tags** | ✅ Yes            | ✅ Yes (Providers) | ❌ No            | ❌ No             |
| **List Injection** | ✅ Yes (`Annotated`)| ✅ Yes (`List`)   | ❌ No            | ⚠️ Manual⁴       |
| **Lazy Loading (`@lazy`)** | ✅ Built-in       | ✅ Yes            | ❌ No            | ❌ No             |
| **Conditional (`@cond`)** | ✅ Full (Profile+) | ✅ Basic          | ❌ No            | ❌ No             |
| **Observability (Context)** | ✅ Built-in       | ❌ Manual         | ❌ Manual        | ❌ Manual         |
| **Observability (Stats)** | ✅ Built-in       | ❌ Manual         | ❌ Manual        | ❌ Manual         |
| **Testing Overrides** | ✅ Built-in       | ✅ Built-in       | ✅ Built-in      | ✅ Via `dependency_overrides` |

**Notes:**
¹ `dependency-injector` can use type hints but primarily relies on its declarative provider syntax.
² `dependency-injector` has async providers, but the core resolution might not be fully non-blocking in all scenarios.
³ FastAPI `Depends` caches results per-request by default, effectively acting as a request singleton.
⁴ List injection in FastAPI usually requires manually yielding dependencies or using custom wrappers.

---

## Philosophical Differences & Use Cases

### `pico-ioc`

* **Focus:** Robustness, Explicit Wiring, Async, Observability, AOP.
* **Philosophy:** Inspired by enterprise Java frameworks (Spring/Guice), prioritizing fail-fast validation, clear architecture, and features needed for complex, long-running applications (like web services). Believes DI is fundamental to the *entire* application, not just the web layer.
* **Strengths:**
    * **Startup Safety:** Catches many errors *before* runtime.
    * **Async Native:** Best-in-class support for `asyncio`.
    * **AOP:** Unique built-in support for cross-cutting concerns.
    * **Tree Configuration:** Powerful `@configured` for complex settings.
    * **Observability:** Designed for multi-container and traceable systems.
* **Weaknesses:**
    * Slightly higher learning curve due to more features.
    * Can feel like "overkill" for very simple scripts.
    * Relies heavily on decorators, which some Python purists dislike.
* **Best For:** Medium-to-large applications, web services, microservices, async applications, multi-tenant systems, projects where robustness and maintainability are critical.

### `dependency-injector`

* **Focus:** Flexibility, Declarative Configuration, Maturity.
* **Philosophy:** Provides a very flexible, declarative way to define providers (often in dedicated `containers.py` files). Less reliant on decorators and type hints directly on business logic classes.
* **Strengths:**
    * Mature and widely used.
    * Flexible provider configuration (factories, singletons, configurations).
    * Good support for different scopes.
* **Weaknesses:**
    * Errors often occur at runtime when a provider is first accessed.
    * Can lead to boilerplate in `containers.py` files.
    * Async support is good but perhaps less deeply integrated than `pico-ioc`.
    * Lacks built-in AOP and advanced tree configuration.
* **Best For:** Projects that prefer explicit, declarative wiring separate from business logic, applications needing flexible provider configurations.

### `punq`

* **Focus:** Simplicity, Type Hint Driven, Minimalist.
* **Philosophy:** Aims to be a very simple, lightweight container that relies almost entirely on type hints and minimal decorators.
* **Strengths:**
    * Very easy to learn and use.
    * Clean integration with type hints.
* **Weaknesses:**
    * Lacks many advanced features (scopes beyond singleton/prototype, async, AOP, configuration, qualifiers, conditional binding).
    * Errors occur at runtime.
* **Best For:** Smaller applications or scripts where only basic DI (constructor injection) is needed and advanced features are unnecessary.

### FastAPI `Depends` (Framework-Native DI)

* **Focus:** Web Layer Dependencies, Request Lifecycle.
* **Philosophy:** Designed specifically to inject dependencies *into web request handlers*. Handles things like path parameters, request bodies, headers, and dependencies that live only for the duration of a request.
* **Strengths:**
    * Perfectly integrated with the FastAPI request lifecycle.
    * Excellent for handling web-specific dependencies.
    * Supports `async` dependencies naturally.
* **Weaknesses:**
    * Not designed for managing application-wide singletons or complex configuration outside the web layer.
    * Lacks features like AOP, qualifiers, advanced conditional logic, or fail-fast validation for the *entire* application graph.
    * Can tightly couple business logic to the web framework if used for everything.
* **Best For:** Handling dependencies directly related to the HTTP request/response cycle within FastAPI. Often used *in combination* with a dedicated DI container like `pico-ioc` for the deeper service layer (see [FastAPI Integration](./integrations/web-fastapi.md)).

---

## Conclusion

`pico-ioc` occupies a specific niche, aiming for the robustness and feature set of enterprise frameworks while embracing modern Python features like `asyncio` and type hints. Its emphasis on **fail-fast validation**, **native async support**, **built-in AOP**, and **advanced configuration binding** makes it a strong choice for complex, production-grade applications where reliability and maintainability are paramount.

---

## Next Steps

This concludes the Architecture section. The final part of the documentation is the API Reference.

* **[API Reference Overview](./api-reference/README.md)**: A quick lookup for all public APIs.

