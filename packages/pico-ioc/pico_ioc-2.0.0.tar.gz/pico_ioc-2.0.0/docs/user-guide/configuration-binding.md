# Configuration Binding (Tree-Based)

While `pico-ioc` supports a basic `@configuration` decorator for flat key-value pairs (see [Basic Configuration](./configuration-basic.md)), the recommended approach for modern applications is the `@configured` decorator.

This system is designed to **bind complex, nested configuration trees** (like JSON or YAML files) directly into graphs of `dataclasses` or other classes.

This allows your application's configuration to be as structured, type-safe, and testable as the rest of your code.

## Core Concepts

The system works by combining three elements:

1.  **A `TreeSource`:** An object that provides the configuration as a nested dictionary. `pico-ioc` provides `JsonTreeSource`, `YamlTreeSource`, and `DictSource` (for testing).
2.  **A Target `dataclass`:** The Python `dataclass` (or class) you want to populate with configuration values.
3.  **The `@configured` Decorator:** This decorator tells `pico-ioc` to register a provider for your `dataclass`.
    * `target`: The `dataclass` to build.
    * `prefix`: The top-level key in your configuration tree to map from.

---

## Basic Binding

Let's start with a simple `config.yml` file:

```yaml
# config.yml
db:
  host: "db.production.local"
  port: 5432
  user: "admin"
  timeout: 15
````

Now, define your `dataclass`es to match this structure:

```python
# settings.py
from dataclasses import dataclass

@dataclass
class DbSettings:
    host: str
    port: int
    user: str
    timeout: int = 30 # Can still have default values
```

Finally, register your component using `@configured` and initialize the container with a `YamlTreeSource`:

```python
# components.py
from pico_ioc import configured, init, YamlTreeSource
from .settings import DbSettings

# This class simply acts as a registration stub.
# It tells pico-ioc: "When someone asks for DbSettings,
# build it using the 'db' prefix from the config tree."
@configured(target=DbSettings, prefix="db")
class ConfiguredDbSettings:
    pass

# app.py
container = init(
    modules=[components],
    tree_config=(YamlTreeSource("config.yml"),)
)

# Now you can get the fully-populated, type-safe settings object
db_settings = container.get(DbSettings)

assert db_settings.host == "db.production.local"
assert db_settings.port == 5432
assert db_settings.timeout == 15 # Value from YAML overrides default
```

-----

## Nested Binding

The real power comes from binding nested structures. The binder will recursively build the entire `dataclass` graph.

```yaml
# config.yml
app:
  cache:
    ttl: 3600
    redis:
      url: "redis://prod-cache:6379"
  auth:
    jwt_secret: "my-super-secret-key"
```

Your `dataclasses` can mirror this structure perfectly:

```python
# settings.py
from dataclasses import dataclass

@dataclass
class RedisConfig:
    url: str

@dataclass
class CacheConfig:
    ttl: int
    redis: RedisConfig # Nested dataclass

@dataclass
class AuthConfig:
    jwt_secret: str

@dataclass
class AppSettings:
    cache: CacheConfig # Nested dataclass
    auth: AuthConfig   # Nested dataclass
```

You only need to register the **root** of the configuration graph you want to inject. `pico-ioc` will handle building the children.

```python
# components.py
from pico_ioc import configured
from .settings import AppSettings

@configured(target=AppSettings, prefix="app")
class ConfiguredAppSettings:
    pass

# app.py
container = init(...)
app_settings = container.get(AppSettings)

assert app_settings.cache.ttl == 3600
assert app_settings.cache.redis.url == "redis://prod-cache:6379"
assert app_settings.auth.jwt_secret == "my-super-secret-key"
```

-----

## Polymorphic Binding (Unions & Discriminators)

The binder also supports `Union` types, allowing you to select one of several `dataclass` implementations from your configuration.

By default, it uses a field named `$type` to "discriminate" which class to build.

```yaml
# config.yml
pet_owner:
  name: "Alice"
  pet:
    $type: "Cat"
    name: "Fluffy"
    lives: 9
```

```python
# settings.py
from dataclasses import dataclass
from typing import Union

@dataclass
class Cat:
    name: str
    lives: int

@dataclass
class Dog:
    name: str
    breed: str

@dataclass
class PetOwner:
    name: str
    pet: Union[Cat, Dog] # The binder will read $type
```

```python
# components.py
@configured(target=PetOwner, prefix="pet_owner")
class ConfiguredPetOwner:
    pass

# app.py
container = init(...)
owner = container.get(PetOwner)

assert isinstance(owner.pet, Cat)
assert owner.pet.name == "Fluffy"
```

### Custom Discriminator

If you don't want to use `$type`, you can specify a custom discriminator field using `Annotated` and `Discriminator`.

```python
# settings.py
from typing import Union, Annotated
from pico_ioc import Discriminator

@dataclass
class PetOwnerCustom:
    name: str
    pet: Annotated[
        Union[Cat, Dog],
        Discriminator("animal_type") # Use 'animal_type' field
    ]
```

Your YAML can now use that field instead:

```yaml
# config.yml
custom_owner:
  name: "Bob"
  pet:
    animal_type: "Dog" # Custom discriminator field
    name: "Buddy"
    breed: "Golden Retriever"
```

```python
# components.py
@configured(target=PetOwnerCustom, prefix="custom_owner")
class ConfiguredCustomOwner:
    pass

# app.py
container = init(...)
owner = container.get(PetOwnerCustom)

assert isinstance(owner.pet, Dog)
assert owner.pet.breed == "Golden Retriever"
```

-----

## Interpolation (Refs & Env Vars)

The configuration tree system supports interpolation for environment variables and references to other parts of the config tree.

  * `${ENV:VAR_NAME}`: Injects the value of the `VAR_NAME` environment variable.
  * `${ref:path.to.key}`: Injects the value from another key in the config tree.

<!-- end list -->

```yaml
# config.yml
defaults:
  user: "default_user"
  host: "localhost"

service:
  # Injects from environment variable DB_HOST
  host: "${ENV:DB_HOST}"
  port: 5432
  # Injects from the 'defaults.user' key above
  user: "${ref:defaults.user}"
```

```python
# settings.py
@dataclass
class ServiceConfig:
    host: str
    port: int
    user: str

# components.py
@configured(target=ServiceConfig, prefix="service")
class ConfiguredService:
    pass

# app.py
import os
os.environ["DB_HOST"] = "prod.db.com"

container = init(...)
config = container.get(ServiceConfig)

assert config.host == "prod.db.com" # From ENV
assert config.user == "default_user" # From ref
```

¡Perfecto\!

El fichero `docs/user-guide/configuration-binding.md` que proporcionaste ya está en un inglés excelente y es muy detallado, así que lo usaremos tal cual.

Continuamos con el siguiente fichero del plan: `docs/user-guide/scopes-lifecycle.md`.

Aquí está la propuesta para `docs/user-guide/scopes-lifecycle.md`. Este fichero es crucial, ya que explica cómo controlar *cuándo* y *con qué frecuencia* se crean y destruyen tus componentes, incluyendo el importante decorador `@lazy`.

-----

````markdown
# Scopes, Lifecycle & @lazy

By default, every component you register is a **`singleton`**. This means `pico-ioc` creates it *once* and shares that exact same instance every time it's injected.

This is often what you want (e.g., for a `DatabaseConnectionPool` or a `UserService`), but not always.

This guide covers how to take full control of your component's **lifecycle** using three mechanisms:

1.  **`@scope`**: Controls *how many* instances are created (one, or many).
2.  **`@lazy`**: Controls *when* a singleton is first created (at startup, or on first use).
3.  **Lifecycle Hooks**: (`@configure`, `@cleanup`) Run code at specific points in a component's life.

---

## 1. Scopes: Controlling Instance Creation

The `@scope` decorator tells `pico-ioc` what instantiation strategy to use for a component.

### `scope("singleton")` (Default)

You don't need to write this, as it's the default. It guarantees only **one instance** of the component will exist within the container.

```python
@component
@scope("singleton") # This is the default
class Database:
    pass

# ---
db1 = container.get(Database)
db2 = container.get(Database)
assert db1 is db2 # True, they are the same object
````

### `scope("prototype")`

A component marked as `prototype` is **created new every single time** it is requested or injected. It is never cached.

This is useful for stateful objects that must not be shared.

```python
@component
@scope("prototype")
class UserRequestState:
    def __init__(self):
        self.user_id = None
        self.data = {}

# ---
req1 = container.get(UserRequestState)
req2 = container.get(UserRequestState)
assert req1 is not req2 # True, they are different objects
```

### `scope("request")` and Custom Scopes

`pico-ioc` also supports context-aware scopes, most commonly used in web applications. `scope("request")` acts like a "per-request singleton."

  * It creates the component **once per request**.
  * It shares that *same* instance for the entire duration of that request.
  * It creates a *new* instance for the next request.

This is perfect for objects like a `RequestContext` that holds the current user's ID or permissions.

```python
@component
@scope("request")
class RequestContext:
    def __init__(self):
        # Logic to get user ID from a token
        self.user_id = get_user_from_http_header() 
        print(f"RequestContext created for {self.user_id}")

@component
class UserService:
    def __init__(self, ctx: RequestContext):
        self.ctx = ctx # Gets the request-scoped context

@component
class OrderService:
    def __init__(self, ctx: RequestContext):
        self.ctx = ctx # Gets the *same* request-scoped context
```

To make this work, you must tell `pico-ioc` when a request begins and ends.

```python
# In your web framework's middleware or request handler
request_id = "req-123"

# Activate the scope with a unique ID
with container.scope("request", request_id):
    # All .get() calls inside this block
    # will share the same RequestContext
    user_svc = container.get(UserService)
    order_svc = container.get(OrderService)
    
    assert user_svc.ctx is order_svc.ctx # True
    
# Outside the block, the "req-123" scope is deactivated
# and its components are eligible for garbage collection.
```

*(See the **Integrations** section for specific recipes for FastAPI, Flask, etc.)*

-----

## 2\. `@lazy`: Deferring Singleton Creation

By default, `pico-ioc` creates all `singleton` components **eagerly** during the `init()` call. This is a key feature—it allows the container to **fail-fast** if a component has missing dependencies or bad configuration.

However, sometimes a component is **very expensive** to create (e.g., it loads a large ML model, or connects to a slow external resource) and you don't want to pay that cost at startup.

Using `@lazy` on a singleton component changes its behavior:

1.  `init()` will **skip** creating this component.
2.  The *first time* `container.get()` is called for this component, it will be created.
3.  All *subsequent* calls will return that same cached instance.

<!-- end list -->

```python
import time
from pico_ioc import component, lazy, init

@component
@lazy
class ExpensiveModel:
    def __init__(self):
        print("Loading model... (this takes 5 seconds)")
        time.sleep(5)
        print("Model loaded!")
        
@component
class MyService:
    def __init__(self, model: ExpensiveModel):
        self.model = model

print("Calling init()...")
container = init(modules=[__name__])
print("init() finished.")

# --- The model has NOT been loaded yet ---

print("Getting MyService...")
# This .get() triggers the creation of ExpensiveModel
service = container.get(MyService)
print("MyService is ready.")

# Output:
# Calling init()...
# init() finished.
# Getting MyService...
# Loading model... (this takes 5 seconds)
# Model loaded!
# MyService is ready.
```

**Use `@lazy` sparingly.** It is a powerful tool for optimizing startup time, but it hides errors. You are trading fail-fast validation at startup for a potential `ComponentCreationError` on the first request.

-----

## 3\. Lifecycle Hooks: `@configure` and `@cleanup`

Sometimes, you need to run logic *after* `__init__` (once all dependencies are injected) or run code *before* the application shuts down.

### `@configure`

A method decorated with `@configure` will be called **immediately after the component is created** and *after* all dependencies are injected into `__init__`.

This is useful for setup logic that *requires* an injected dependency.

```python
@component
class DatabaseConnection:
    def __init__(self, config: DbConfig):
        self.config = config
        # self.connection is not yet established
        
    @configure
    def connect(self):
        # This runs after __init__
        # We can use self.config here
        print(f"Connecting to {self.config.URL}...")
        self.connection = self.establish_connection(self.config.URL)

    def establish_connection(self, url): ...
```

### `@cleanup`

A method decorated with `@cleanup` will be called when you explicitly tell the container to shut down by calling **`container.cleanup_all()`** (or `container.cleanup_all_async()`).

This is essential for gracefully releasing resources like database connections, file handles, or background threads.

```python
@component
class ConnectionPool:
    def __init__(self):
        self.pool = self.create_pool()
        print("Connection pool created.")

    @cleanup
    def close_pool(self):
        # This runs when container.cleanup_all() is called
        print("Closing all connections in the pool...")
        self.pool.close()

    def create_pool(self): ...

# --- In your main.py ---
container = init(...)
pool = container.get(ConnectionPool)

# ... your application runs ...

print("Application shutting down...")
container.cleanup_all()

# Output:
# Connection pool created.
# Application shutting down...
# Closing all connections in the pool...
```

*(See the **Advanced Features** section for details on async `@cleanup` methods.)*

-----

## Next Steps

You now know how to control the lifecycle of your components. The next step is to learn how to handle situations where you have *multiple* implementations for a single interface.

  * **[Qualifiers & List Injection](./qualifiers-lists.md)**: Learn how to tag components and inject specific lists of them.


