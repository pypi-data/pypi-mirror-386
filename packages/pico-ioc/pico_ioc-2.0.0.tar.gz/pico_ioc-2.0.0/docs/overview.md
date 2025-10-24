# Pico IOC: A Python Dependency Injection Framework

## 1. Overview

**Pico IOC** is a Dependency Injection (DI) container for Python that implements advanced enterprise architecture patterns. Its design is inspired by frameworks like Spring (Java) and Guice, adapted for the Python ecosystem.

It provides a robust, type-safe, and testable foundation for complex applications by managing component lifecycles, configuration, and runtime dependencies.

---

## 2. Core Features

* ✅ **Type Safety**: Extensive use of type hints and generics.
* ✅ **Robust Error Handling**: Provides `CircularDependencyError` with the full chain and `InvalidBindingError` at startup.
* ✅ **Startup Validation**: Detects missing bindings during initialization, not at runtime.
* ✅ **Async-Native**: Full support for async resolution (`aget`), async-aware AOP, and async lifecycle hooks.
* ✅ **Serializable Proxies**: Lazy and AOP proxies are serializable via `pickle`.
* ✅ **Native AOP**: Supports method interception without bytecode manipulation.
* ✅ **Sophisticated Scopes**: `singleton`, `prototype`, and `ContextVar`-based scopes (e.g., `request`, `session`).
* ✅ **Typed Configuration**: Injects configuration from environment/files into `dataclasses`.
* ✅ **Testing-friendly**: Built-in support for overrides and profiles.
* ✅ **Event-Driven**: Includes a built-in async event bus.

---

## 3. Getting Started: A Simple Example

```python
from dataclasses import dataclass
from pico_ioc import component, init

# 1. Define your components
class Greeter:
    def say_hello(self) -> str: ...

@component
class EnglishGreeter(Greeter):
    def say_hello(self) -> str:
        return "Hello!"

@component
class App:
    # 2. Declare dependencies in the constructor
    def __init__(self, greeter: Greeter):
        self.greeter = greeter
    
    def run(self):
        print(self.greeter.say_hello())

# 3. Initialize the container
# The 'modules' list tells pico_ioc where to scan for @component
container = init(modules=[__name__])

# 4. Get the root component and run
app = container.get(App)
app.run()

# Output: Hello!
````

-----

## 4\. Recommended Use Cases

  * ✅ **Ideal for**:
      * Web applications (Flask/FastAPI with request/session scopes).
      * Microservices (multi-environment configuration, event bus).
      * Complex testing (mocks with overrides).
      * Auditing/logging (AOP interceptors).
      * Modular, event-driven architectures.
  * ❌ **Avoid in**:
      * Simple scripts (unnecessary overhead).
      * Extreme high-performance critical paths (reflection cost).

-----

## 5\. Conclusion

Pico IOC is a mature, robust, and feature-rich DI framework. Its strong support for async operations, startup validation, and cycle detection makes it a reliable choice for complex, modern applications.

