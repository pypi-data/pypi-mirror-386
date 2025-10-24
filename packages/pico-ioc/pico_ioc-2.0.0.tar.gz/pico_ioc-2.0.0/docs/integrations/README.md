# Integrations

`pico-ioc` is not a web framework—it's a powerful companion *for* web frameworks.

Modern frameworks like FastAPI and Flask provide their own simple, built-in dependency injection systems (e.g., FastAPI's `Depends`). These systems are excellent for handling web-layer dependencies, like route parameters, cookies, and request bodies.

However, as your application grows, you'll develop a deep stack of **business logic** (services, repositories, clients) that has *nothing* to do with the web. This is where `pico-ioc` shines.

By combining `pico-ioc` with your web framework, you get the best of both worlds:
* **Your framework** handles **web-layer concerns** (HTTP requests, JSON parsing).
* **`pico-ioc`** handles your **application-layer concerns** (business logic, services, database connections).

This separation makes your application:
* ✅ **More Testable:** You can test your `UserService` in isolation without needing to mock an entire HTTP request.
* ✅ **More Portable:** Your core business logic isn't tied to FastAPI. You could move it to a CLI, a background worker, or a different web framework.
* ✅ **Better Structured:** `pico-ioc`'s advanced features (like `@factory`, `@qualifier`, and `@conditional`) provide a robust structure that simple DI systems lack.
* ✅ **Easier to Configure:** Manage your application's entire configuration (DB URLs, API keys) in one place using `pico-ioc`'s configuration binding.

---

## In This Section

This section provides practical, copy-paste recipes for integrating `pico-ioc` with popular frameworks and tools.

* **[FastAPI](./web-fastapi.md)**
    * How to initialize the container at startup.
    * How to manage `request` scopes using middleware.
    * How to create a `Depends`-compatible function to inject your services into routes.

* **[Flask](./web-flask.md)**
    * How to attach the container to the `app` object.
    * How to use `before_request` and `teardown_request` to manage scopes.
    * How to inject services into your Flask `views`.

* **[Django](./web-django.md)**
    * How to initialize the `pico-ioc` container in your `AppConfig.ready()`.
    * How to use `pico-ioc` for your *service layer*, keeping it separate from the Django ORM and views.

* **[AI & LangChain](./ai-langchain.md)**
    * A pattern for managing complex AI applications.
    * How to register `LLMs`, `Retrievers`, and `Tools` as configurable components.
    * How to use `pico-ioc` to build and test different `Chains` and `Agents`.

---

## Next Steps

Let's start with the most popular modern web framework:

* **[FastAPI](./web-fastapi.md)**: Learn the standard pattern for integrating `pico-ioc` with a FastAPI application.

