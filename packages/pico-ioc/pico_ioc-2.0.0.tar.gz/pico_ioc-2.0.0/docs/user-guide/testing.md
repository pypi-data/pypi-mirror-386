# Testing Applications

One of the greatest benefits of using Dependency Injection is that your code becomes **highly testable**.

Because your components are loosely coupled (your `UserService` just depends on the `Database` *interface*, not a concrete `PostgresDatabase`), you can easily swap the *real* implementation for a *fake* one during tests.

`pico-ioc` provides two primary patterns for achieving this:

1.  **Overrides:** Ideal for **unit testing**. You surgically replace a specific component (like a `Database`) with a mock object for a single test.
2.  **Profiles:** Ideal for **integration testing**. You create a dedicated "test" profile that configures your container to use a full set of test-friendly components (like an in-memory database or a mock payment service).

---

## 1. The "Overrides" Pattern (for Mocking)

This is the simplest and most common way to write a unit test. You use the `init(overrides={...})` argument to provide a dictionary of "replacements."

**Problem:** You want to test `UserService`, but it depends on the real `Database`. You don't want your unit test to make actual network calls. You want to replace `Database` with a `MockDatabase`.

### Step 1: Your Application Code

First, let's look at the real components.

```python
# app/services.py
from typing import Protocol
from pico_ioc import component

class Database(Protocol):
    def get_user(self, user_id: int) -> str: ...

@component
class PostgresDatabase(Database):
    def get_user(self, user_id: int) -> str:
        # ... logic to connect to a real Postgres DB
        print("Connecting to REAL Postgres...")
        return f"User {user_id} (from DB)"

@component
class UserService:
    def __init__(self, db: Database):
        self.db = db
        
    def get_username(self, user_id: int) -> str:
        username = self.db.get_user(user_id)
        return username.upper()
````

### Step 2: Your Test File

In your test, you define a `MockDatabase` and tell `init()` to use it instead of `PostgresDatabase` whenever a `Database` is requested.

```python
# tests/test_user_service.py
import pytest
from pico_ioc import init
from app.services import UserService, Database

# 1. Define your mock object
class MockDatabase(Database):
    def get_user(self, user_id: int) -> str:
        print("Using MOCK Database!")
        return f"Mock User {user_id}"

@pytest.fixture
def test_container():
    """A pytest fixture to create a container for each test."""
    
    # 2. Use 'overrides' to replace the real component
    container = init(
        modules=["app.services"],
        overrides={
            # When any component asks for 'Database',
            # give them this 'MockDatabase' instance instead.
            Database: MockDatabase()
        }
    )
    return container

# 3. Write your test
def test_user_service_with_mock(test_container):
    # Get the UserService from the *overridden* container
    service = test_container.get(UserService)
    
    # The 'service.db' instance is now our MockDatabase
    username = service.get_username(123)
    
    # Assert against the mock's return value
    assert username == "MOCK USER 123"
```

When this test runs, `pico-ioc` builds the container and sees the override. When it creates `UserService`, it sees it needs a `Database`. Instead of providing `PostgresDatabase` (the `@primary` component), it injects your `MockDatabase()` instance.

-----

## 2\. The "Profiles" Pattern (for Environments)

Overrides are great for small tests. But what if you want to run your *entire application* against a suite of test-friendly services (e.g., an in-memory SQLite database, a mock email sender, and an in-memory cache)?

This is where **profiles** shine. You use `init(profiles=(...))` to activate a profile, and `@conditional` to tell your components which profile they belong to.

**Problem:** You want a "prod" environment that uses the real `RedisCache`, but a "test" environment that automatically uses a simple `InMemoryCache`.

### Step 1: Your Application Code

You define *both* implementations, but use `@conditional` and `@on_missing` to control which one is active.

```python
# app/cache.py
from typing import Protocol
from pico_ioc import component, conditional, on_missing

class Cache(Protocol):
    def set(self, key: str, value: str): ...

@component
@conditional(profiles=("prod",)) # Only active if "prod" profile is passed to init()
class RedisCache(Cache):
    def set(self, key: str, value: str):
        print("Setting key in REAL Redis...")
        # ... real redis logic ...

@component
@on_missing(Cache) # Activates IF no other Cache was registered
class InMemoryCache(Cache):
    """This is the default/fallback cache for 'dev' or 'test'."""
    def __init__(self):
        self.data = {}
        
    def set(self, key: str, value: str):
        print(f"Setting key '{key}' in FAKE in-memory cache.")
        self.data[key] = value

@component
class CacheService:
    def __init__(self, cache: Cache):
        self.cache = cache # Will get RedisCache or InMemoryCache
        
    def cache_user(self, user_id: int):
        self.cache.set(f"user:{user_id}", "data")
```

### Step 2: Your `conftest.py`

In your `conftest.py`, you define a `pytest` fixture that initializes the container *with the "test" profile active*.

```python
# tests/conftest.py
import pytest
from pico_ioc import init, PicoContainer

@pytest.fixture(scope="session")
def test_container() -> PicoContainer:
    """A single container for the entire test session."""
    
    # 2. Initialize using the "test" profile
    container = init(
        modules=["app.cache"],
        profiles=("test",) # This activates the "test" profile
    )
    yield container
    
    # (Optional) Clean up after all tests are done
    container.cleanup_all()
```

### Step 3: Your Test File

Your test file is now incredibly simple. It just uses the `test_container` fixture. It doesn't need to know *anything* about mocking, because the container was already built correctly for testing.

```python
# tests/test_cache_service.py

def test_cache_service_uses_in_memory(test_container):
    # 'test_container' was built with the "test" profile
    # 'RedisCache' was skipped (it needs "prod")
    # 'InMemoryCache' was activated (due to @on_missing(Cache))
    
    service = test_container.get(CacheService)
    
    service.cache_user(123)
    
    # We can verify that the in-memory cache was used
    assert isinstance(service.cache, InMemoryCache)
    assert service.cache.data["user:123"] == "data"
```

-----

## 3\. Summary: Which Pattern to Use?

| Pattern | `init(overrides={...})` | `init(profiles=(...))` |
| :--- | :--- | :--- |
| **Best For** | **Unit Tests** | **Integration / E2E Tests** |
| **What it does** | Surgically replaces components *after* they are discovered. | Controls which components are *discovered* in the first place. |
| **Analogy** | Using a stunt double for one specific scene. | Filming the entire movie with a different actor. |
| **Example** | `overrides={Database: MockDatabase()}` | `profiles=("test",)` |

-----

## Next Steps

You've now mastered the core User Guide\! You can build, configure, and test complex applications.

You're ready to explore the **[Advanced Features](./advanced-features/README.md)** section to add powerful capabilities like AOP, async event handling, and health checks to your application.

