# 📦 Pico-IoC: A Robust, Async-Native IoC Container for Python

[![PyPI](https://img.shields.io/pypi/v/pico-ioc.svg)](https://pypi.org/project/pico-ioc/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-ioc)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-ioc/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-ioc/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-ioc)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-ioc&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-ioc)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-ioc&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-ioc)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-ioc&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-ioc)

**pico-ioc** is a **robust, async-native, decorator-based IoC container for Python**.
It helps you build loosely-coupled, testable, enterprise-grade applications without manual wiring. Inspired by the Spring ecosystem, but fully Pythonic.

> ⚠️ **Requires Python 3.10+** (due to extensive use of modern `typing` features).

---

## ⚖️ Principles

* **Focus & Simplicity**: A declarative API for one job: managing dependencies. It avoids accidental complexity by doing one thing well.
* **Declarative & Explicit**: No magic. Behavior is deterministic, relying on explicit decorators (`@component`, `@factory`) and type hints.
* **Unified Composition Root**: The application is assembled from a single entry point (`init`) which defines a clear, predictable boundary.
* **Fail-Fast by Design**: Catches **circular dependencies** and **missing bindings** at startup, not at runtime. If the application runs, it's wired correctly.
* **Testability First**: Features like `@conditional`, profiles, and `overrides` are first-class citizens, enabling fast and isolated testing.
* **Async Native & Extensible**: Full `async`/`await` support, AOP (`@intercepted_by`), and a built-in `EventBus` are available out-of-the-box.
* **Framework Agnostic**: Zero hard dependencies (standard library only). It works with any Python application, from simple scripts to complex web servers.

---

## ✨ Why Pico-IoC?

`pico-ioc` exists to solve a common problem that arises as Python applications grow: managing how objects are created and connected becomes complex and brittle. This manual wiring, where a change deep in the application can cause a cascade of updates, makes the code hard to test and maintain.

`pico-ioc` introduces the principle of Inversion of Control (IoC) in a simple, Pythonic way. Instead of you creating and connecting every object, you declare your components with a simple `@component` decorator, and the container automatically wires them together based on their type hints. It brings the architectural robustness and testability of mature frameworks like Spring to the Python ecosystem, allowing you to build complex, loosely-coupled applications that remain simple to manage.

| Feature | Manual Wiring | With Pico-IoC |
| :--- | :--- | :--- |
| **Object Creation** | `service = Service(Repo(Config()))` | `svc = container.get(Service)` |
| **Testing** | Manual replacement or monkey-patching | `overrides={Repo: FakeRepo()}` |
| **Coupling** | High (code knows about constructors) | Low (code just asks for a type) |
| **Maintenance** | Brittle (changing a constructor breaks consumers) | Robust (changes are isolated) |
| **Learning Curve** | Ad-hoc, implicit patterns | Uniform, explicit, documented |

---

## 🧩 Features

### Core

* **Zero external dependencies** — pure Python, framework-agnostic.
* **Decorator-based API** — `@component`, `@factory`, `@provides`, `@configuration`.
* **Fail-fast Bootstrap** — Detects **circular dependencies** and **missing bindings** at startup.
* **Async-Native Resolution** — Full `async`/`await` support with `container.aget()`.
* **Sophisticated Scopes** — `singleton`, `prototype`, and `ContextVar`-based scopes (e.g., `request`, `session`).
* **Typed Configuration** — Injects `dataclasses` from environment/files via `@configuration`.
* **Test-Driven** — Built-in `overrides` and `profiles` for easy mocking.

### Advanced

* **AOP / Interceptors** — Intercept method calls with `@intercepted_by`.
* **Qualifiers** — Inject subsets of components with `Annotated[List[T], Qualifier(...)]`.
* **Async Event Bus** — Built-in `EventBus` for decoupled, event-driven architecture.
* **Conditional Registration** — `@conditional` (by profile, env var) and `@on_missing` (fallbacks).
* **Lifecycle Hooks** — `@configure` (post-init) and `@cleanup` (on shutdown).
* **Health Checks** — Built-in `@health` decorator and `container.health_check()`.
* **Serializable Proxies** — Lazy (`@lazy`) and AOP proxies are `pickle`-safe.

---

## 📦 Installation

```bash
# Requires Python 3.10+
pip install pico-ioc
````

-----

## 🚀 Quick Start

```python
from pico_ioc import component, init, configuration
from dataclasses import dataclass

@configuration
@dataclass
class Config:
    url: str = "sqlite:///demo.db"

@component
class Repo:
    def __init__(self, cfg: Config):
        self.url = cfg.url
    def fetch(self): 
        return f"fetching from {self.url}"

@component
class Service:
    def __init__(self, repo: Repo):
        self.repo = repo
    def run(self): 
        return self.repo.fetch()

# Bootstrap the container by scanning modules
# We use __name__ to scan the current module
container = init(modules=[__name__])

# Resolve the service and run
svc = container.get(Service)
print(svc.run())
```

**Output:**

```
fetching from sqlite:///demo.db
```

-----

### Quick Overrides for Testing

The `init` function accepts `overrides` to replace any component for testing.

```python
import my_app_module
from pico_ioc import init

# Define a fake repository
class FakeRepo:
    def fetch(self): 
        return "fake-data"

# Initialize the container, overriding the real Repo
container = init(
    modules=[my_app_module],
    overrides={
        Repo: FakeRepo()  # Override by type
    }
)

# The service now receives FakeRepo instead of the real one
svc = container.get(Service)
assert svc.run() == "fake-data"
```

-----

## 📖 Documentation

  * **🚀 New to pico-ioc? Start with the User Guide.**

      * [**guide.md**](.docs/guide.md) — Learn with practical examples: testing, configuration, AOP, async, and web framework integration.

  * **🏗️ Want to understand the internals? See the Architecture.**

      * [**architecture.md**](./docs/architecture.md) — A deep dive into the resolution algorithm, lifecycle, and internal design.

-----

## 🧪 Development

```bash
pip install tox
tox
```

-----

## 📜 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

-----

## 📜 License

MIT — see [LICENSE](https://opensource.org/licenses/MIT)

```
```


