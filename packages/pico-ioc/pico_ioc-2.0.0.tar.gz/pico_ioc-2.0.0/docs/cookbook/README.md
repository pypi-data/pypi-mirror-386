# Cookbook (Patterns)

Welcome to the `pico-ioc` Cookbook. 🧑‍🍳

The [User Guide](./user-guide/README.md) showed you the *features* (like `@scope` or `@factory`).
The [Integrations](./integrations/README.md) section showed you *recipes* for specific frameworks (like Flask or FastAPI).

This section is different. It provides complete, end-to-end **architectural patterns**. These are solutions to high-level design problems, showing how all of `pico-ioc`'s features come together to build a robust, production-grade application.

The examples here are designed to be a source of inspiration and a "copy-paste" starting point for your own projects.

---

## In This Section

### [1. Pattern: Multi-Tenant Applications](./pattern-multi-tenant.md)

**Problem:** You need to build a SaaS application where each of your customers (tenants) has its own isolated data, configuration, and services, all running within the same Python process.

**Solution:** This pattern shows you how to leverage the [Container Context](./observability/container-context.md) system. You'll learn how to create and manage a separate, isolated `PicoContainer` for each tenant, and how to use middleware to activate the correct container for each incoming request.

### [2. Pattern: Hot Reload (Dev Server)](./pattern-hot-reload.md)

**Problem:** You're in development, and every time you change a service file, you have to manually stop and restart your server to see the changes.

**Solution:** This pattern demonstrates how to use `container.shutdown()` and `init()` to create a "hot-reload" server. You'll learn how to watch your project files and automatically destroy the old container and build a new one, all without killing the main server process.

### [3. Pattern: CLI Applications](./pattern-cli-app.md)

**Problem:** You're building a complex command-line tool (e.g., with `Click` or `Typer`), not a web app. You still want to use DI to manage your services, configuration, and database connections.

**Solution:** This guide provides a clean structure for building a CLI. You'll learn how to initialize the container in your `main()` function, inject services into your commands, and manage configuration from files and environment variables.

---

## Next Steps

Let's dive into the first and most advanced pattern:

* **[Pattern: Multi-Tenant Applications](./pattern-multi-tenant.md)**: Learn how to build an isolated, multi-tenant architecture.

