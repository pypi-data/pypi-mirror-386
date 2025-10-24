# Advanced: Conditional Binding

In a real application, you don't always want the same set of components.
* In **production**, you want the real `PostgresDatabase`.
* In **development**, you might want a local `SqliteDatabase`.
* In **testing**, you want a completely fake `MockDatabase`.

`pico-ioc` allows you to define all of these implementations and then use **conditional binding** to control which one is active when you call `init()`.

This is handled by three decorators:

1.  **`@primary`**: The simplest. When multiple components implement one interface, this one is the "default" choice.
2.  **`@on_missing`**: A fallback. This component only registers if *no other implementation* is found.
3.  **`@conditional`**: The most powerful. This component only registers if complex rules (based on profiles, environment variables, or custom functions) are met.

---

## 1. `@primary`: The "Default" Choice

**Problem:** You have one interface and multiple implementations. If a component just asks for the interface, how does `pico-ioc` know which one to inject?

```python
class Database(Protocol): ...

@component
class PostgresDatabase(Database): ...

@component
class SqliteDatabase(Database): ...

@component
class UserService:
    def __init__(self, db: Database):
        # Which one does 'db' get? Postgres or Sqlite?
        self.db = db
````

This causes an `InvalidBindingError` at startup because `pico-ioc` sees the ambiguity.

**Solution:** You use `@primary` to mark one implementation as the default.

```python
@component
@primary  # <-- This is the default
class PostgresDatabase(Database): ...

@component
class SqliteDatabase(Database): ...

@component
class UserService:
    def __init__(self, db: Database):
        # 'db' will now receive PostgresDatabase
        self.db = db
```

-----

## 2\. `@on_missing`: The "Fallback" Choice

**Problem:** You want to provide a sensible default (like an in-memory cache) that is *only* used if no "real" implementation (like `RedisCache`) is registered. This is perfect for testing or development.

**Solution:** Use `@on_missing`. This decorator registers a component *only if* no other component is registered for its key (or a type it implements).

Let's see how this works with **profiles**, which we covered in the [Testing Guide](./user-guide/testing.md).

### Step 1: Define the "Real" and "Fallback" Components

```python
# cache.py
class Cache(Protocol): ...

@component
@conditional(profiles=("prod",)) # <-- Only active in "prod"
class RedisCache(Cache):
    ...
    print("Real RedisCache registered")

@component
@on_missing(Cache) # <-- Activates if no other 'Cache' is found
class InMemoryCache(Cache):
    ...
    print("Fallback InMemoryCache registered")
```

### Step 2: Initialize with Different Profiles

Now, watch what happens when we change the `profiles` tuple during `init()`.

#### Production Environment:

```python
# init(profiles=("prod",))
container = init(modules=["cache"], profiles=("prod",))
cache = container.get(Cache)

# Output:
# Real RedisCache registered
# (InMemoryCache is never registered)
```

In this case, `RedisCache` is registered first. When `pico-ioc` checks `InMemoryCache`, it sees that a `Cache` component *already exists*, so `@on_missing` causes it to be skipped.

#### Test/Dev Environment:

```python
# init(profiles=("test",))
container = init(modules=["cache"], profiles=("test",))
cache = container.get(Cache)

# Output:
# Fallback InMemoryCache registered
```

In this case, `RedisCache` is skipped (its `@conditional` fails). When `pico-ioc` checks `InMemoryCache`, it sees that *no other `Cache` component exists*, so `@on_missing` allows it to be registered.

-----

## 3\. `@conditional`: The "Rules-Based" Choice

This is the most powerful decorator. It lets you register a component based on a complex set of rules.

It takes three arguments, all of which must be true:

  * `profiles: Tuple[str, ...]`
  * `require_env: Tuple[str, ...]`
  * `predicate: Callable[[], bool]`

### Example 1: Conditional on Profile

This is the most common use. The component is only registered if one of the listed profiles is active.

```python
@component
@conditional(profiles=("prod", "staging"))
class RealPaymentService(PaymentService):
    ...
```

`container = init(profiles=("prod",))` will register this.
`container = init(profiles=("dev",))` will **not**.

### Example 2: Conditional on Environment Variable

The component is only registered if the environment variable exists and is *not* empty or `None`.

```python
@component
@conditional(require_env=("ENABLE_BETA_FEATURES",))
class BetaFeatureService:
    ...
```

This service will only be registered if you run your app with `ENABLE_BETA_FEATURES=true python app.py`.

### Example 3: Conditional on Predicate

You can provide a custom function. The component is only registered if the function returns `True`.

```python
import os

def is_analytics_enabled():
    # You can run any complex logic here
    return os.environ.get("ANALYTICS_KEY") is not None

@component
@conditional(predicate=is_analytics_enabled)
class AnalyticsService:
    ...
```

### Example 4: Combining All Rules

You can combine all rules. The component is only registered if **all conditions are met**.

```python
@component
@conditional(
    profiles=("prod",),
    require_env=("STRIPE_API_KEY",),
    predicate=is_stripe_enabled
)
class StripePaymentProvider:
    ...
```

This component will only be registered if:

1.  The active profile is "prod" **AND**
2.  The `STRIPE_API_KEY` environment variable is set **AND**
3.  The `is_stripe_enabled()` function returns `True`.

-----

## Next Steps

You've now seen how to control your application's architecture based on its environment. The final piece of the advanced puzzle is monitoring your application's health.

  * **[Health Checks](./health-checks.md)**: Learn how to use the `@health` decorator to create a simple, aggregated health report for your application.

```
