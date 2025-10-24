# Observability: Exporting the Dependency Graph

As your application grows to hundreds of components, it becomes difficult to understand the complex web of dependencies. You might ask:

* "What is the full dependency chain for my `PaymentService`?"
* "Why is `LegacyService` being loaded? What depends on it?"
* "I have a `CircularDependencyError`, but the text chain is too complex to follow."

**Problem:** You can't *see* your application's architecture.

**Solution:** `pico-ioc` can export its complete dependency graph as a `.dot` file. This file is a plain text description of a graph that can be rendered into a visual diagram using tools like **Graphviz**.

This gives you a bird's-eye view of your entire application, making it an incredibly powerful tool for debugging, refactoring, and documentation.

---

## 1. How to Export the Graph

The `PicoContainer` object has a `export_graph()` method.

**Note:** This feature requires an optional dependency, `graphviz`. Install it first:

```bash
pip install pico-ioc[graphviz]
````

Once installed, you can call the method after your container is initialized:

```python
from pico_ioc import init

container = init(modules=["my_app.services", "my_app.database"])

# Exports the graph to a file named 'dependency_graph.dot'
dot_filename = container.export_graph(
    filename="dependency_graph",
    output_dir="."
)

print(f"Graph exported to: {dot_filename}")
```

This will create a `dependency_graph.dot` file in your directory.

-----

## 2\. How to View the Graph

A `.dot` file is a text file. To turn it into an image (like a `.png` or `.svg`), you need the **Graphviz** command-line tools. (You can download them from [graphviz.org](https://graphviz.org/download/)).

Once Graphviz is installed, you can use the `dot` command to render your graph:

```bash
# This converts the .dot file into a PNG image
dot -Tpng dependency_graph.dot -o dependency_graph.png
```

This will create `dependency_graph.png`, which you can open to see your application's architecture.

-----

## 3\. Example

Let's imagine a small application:

```python
# app.py
from pico_ioc import component

@component
class Config: ...

@component
class Database:
    def __init__(self, config: Config): ...

@component
class UserService:
    def __init__(self, db: Database): ...

@component
class App:
    def __init__(self, user_service: UserService, config: Config): ...
```

Running `container.export_graph()` and `dot -Tpng ...` would generate an image that looks something like this:

```text
┌───────────┐      ┌───────────────┐
│    App    │ ───> │  UserService  │
└───────────┘      └───────────────┘
       │                   │
       │                   │
       ▼                   ▼
┌───────────┐      ┌───────────┐
│   Config  │ <─── │  Database │
└───────────┘      └───────────┘
```

**Key features of the graph:**

  * **Nodes:** Represent your components (e.g., `App`, `UserService`).
  * **Edges (Arrows):** Represent dependencies. An arrow from `App` to `UserService` means "App depends on UserService."
  * **Scopes & Qualifiers:** The graph will also render metadata like `@scope("request")` or `@qualifier(PAYMENT)` on the nodes, so you can see your architecture at a glance.

This visual map is invaluable for spotting circular dependencies, identifying overly-complex components (too many arrows pointing out), or finding services that can be refactored.

-----

## Next Steps

This concludes the section on Observability. You now know how to manage container contexts, get metrics, trace resolutions, and visualize your entire application.

The next section provides practical, copy-paste recipes for integrating `pico-ioc` with popular web frameworks.

  * **[Integrations Overview](./integrations/README.md)**: Learn how to use `pico-ioc` with FastAPI, Flask, and more.

