# Pico IOC: Developer Guide

This guide covers the primary features of Pico IOC from a user's perspective, focusing on how to accomplish common tasks.

## 1. Registering Components

### 1.1. `@component`

The `@component` decorator is the most common way to register a class.

```python
@component
class MyService:
    def __init__(self, dep: AnotherService):
        self.dep = dep
````

By default, this registers the component as a `singleton` keyed by its class type (`MyService`).

### 1.2. `@factory` and `@provides`

For complex creation logic or 3rd-party objects, use a `@factory`.

```python
@factory
class DatabaseFactory:
    
    # The factory itself can have dependencies
    def __init__(self, config: AppConfig):
        self.db_url = config.DB_URL

    @provides(DatabaseConnection)
    def create_db(self) -> DatabaseConnection:
        # Complex logic
        conn = connect(self.db_url)
        return conn
```

This registers a provider for `DatabaseConnection`.

-----

## 2\. Configuration with `@configuration`

Pico IOC can inject configuration from environment variables or files into a `dataclass`.

```python
@configuration(prefix="APP_")
@dataclass
class AppConfig:
    DEBUG: bool = False
    TIMEOUT: int = 30

# In main.py
container = init(
    modules=[...],
    config=(EnvSource(), FileSource("config.json"))
)

# Usage
@component
class NeedsConfig:
    def __init__(self, config: AppConfig):
        # config.DEBUG is auto-populated
        self.config = config
```

This will look for `APP_DEBUG` and `APP_TIMEOUT` in the environment or file.

-----

## 3\. Controlling Injection

### 3.1. `@primary`

When multiple components implement the same interface, `@primary` marks the default one.

```python
class Database(Protocol): ...

@component
@primary
class PostgresDB(Database): pass

@component
class MySQLDB(Database): pass

@component
class Service:
    # This will receive PostgresDB
    def __init__(self, db: Database):
        self.db = db
```

### 3.2. `@conditional`

This decorator only registers a component if certain conditions are met.

```python
# Only active if 'prod' profile is used AND REDIS_URL is set
@component
@conditional(profiles=("prod",), require_env=("REDIS_URL",))
class RedisCache(Cache): pass
```

### 3.3. `@on_missing`

This registers a component only if no other component is registered for its key (or a compatible type).

```python
# Used as a fallback, e.g., for testing
@component
@on_missing(Cache, priority=10)
class InMemoryCache(Cache): pass
```

### 3.4. `@lazy`

This defers the creation of a component until it is first used.

```python
@component
@lazy
class ExpensiveService:
    def __init__(self):
        # This code won't run until a method
        # on ExpensiveService is called.
        self.data = load_huge_dataset()
```

-----

## 4\. Lifecycle and Scopes

### 4.1. `@scope`

You can control the component's lifecycle.

```python
@component
@scope("request")
class RequestData:
    # This class will be a per-request singleton
    pass
```

  * `singleton` (default): One instance for the container's lifetime.
  * `prototype`: A new instance is created every time it's requested.
  * `request`, `session`: `ContextVar`-based scopes for web applications.

### 4.2. `@configure` and `@cleanup`

You can define methods to be called during the component's lifecycle.

```python
@component
class DatabaseConnection:
    @configure
    def setup(self):
        # Called after __init__
        self.conn.open()

    @cleanup
    def close(self):
        # Called when container.cleanup_all() is invoked
        self.conn.close()
```

-----

## 5\. Qualifiers

Qualifiers are used to inject specific subsets of implementations.

```python
PAYMENT = Qualifier("payment")
MESSAGING = Qualifier("messaging")

@component
@qualifier(PAYMENT)
class StripeSender(Sender): pass

@component
@qualifier(MESSAGING)
class EmailSender(Sender): pass

@component
class PaymentService:
    def __init__(
        # Injects a list of all Senders marked with 'payment'
        self, 
        senders: Annotated[List[Sender], PAYMENT]
    ):
        self.senders = senders # [StripeSender()]
```

-----

## 6\. Aspect-Oriented Programming (AOP)

AOP allows you to intercept method calls.

**1. Define the Interceptor:**

```python
@component
class AuditInterceptor(MethodInterceptor):
    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        log.info(f"Before: {ctx.name}")
        result = call_next(ctx) # Calls the original method
        log.info(f"After: {ctx.name}")
        return result
```

**2. Apply the Interceptor:**

```python
@component
class UserService:
    @intercepted_by(AuditInterceptor)
    def create_user(self, name: str):
        return User(name)
```

When `create_user` is called, `AuditInterceptor.invoke` will run.

-----

## 7\. Event Bus

Pico IOC includes a built-in async event bus.

**1. Define an Event:**

```python
@dataclass
class UserCreatedEvent(Event):
    user_id: int
```

**2. Subscribe to the Event:**

```python
@component
class UserEventHandler:
    # Must be registered with the container
    def __init__(self, bus: EventBus):
        bus.subscribe(UserCreatedEvent, self.on_user_created)
    
    async def on_user_created(self, event: UserCreatedEvent):
        print(f"Sending welcome email to user {event.user_id}")
```

**3. Publish the Event:**

```python
@component
class UserService:
    def __init__(self, bus: EventBus):
        self.bus = bus
    
    async def create_user(self, name: str) -> User:
        user = ... # Save to DB
        await self.bus.publish(UserCreatedEvent(user_id=user.id))
        return user
```

The container automatically provides the `EventBus` instance.

-----

## 8\. Health Checks

Define health checks with the `@health` decorator.

```python
@component
class DatabaseConnection:
    @health
    def check_connection(self) -> bool:
        return self.conn.is_alive()

# Check all registered health checks
status = container.health_check()
# status -> {"DatabaseConnection.check_connection": True}
```

-----

## 9\. Testing

Pico IOC is designed for testability.

### 9.1. Overrides

You can replace components at initialization.

```python
# In your test
class MockDB(Database):
    def query(self, sql): return "mocked_data"

container = init(
    modules=["my_app"],
    overrides={
        Database: MockDB(), # Replace Database with MockDB
        "api_key": "test-key-123" # Replace string keys
    }
)

service = container.get(MyService)
# service.db is now an instance of MockDB
```

### 9.2. Profiles

Use profiles to conditionally register components (like mocks or real services).

```python
# In conftest.py
@pytest.fixture
def test_container():
    # 'test' profile is active
    return init(modules=["my_app"], profiles=("test",))

# In your component file
@component
@conditional(profiles=("prod",))
class RealPaymentService(PaymentService): pass

@component
@conditional(profiles=("test",))
class MockPaymentService(PaymentService): pass
```

The `test_container` will only contain `MockPaymentService`.

-----

## 10\. Full Architecture Example

```python
# domain/models.py
@dataclass
class User:
    id: int
    email: str

# infrastructure/database.py
class UserRepository(Protocol):
    def find_by_id(self, user_id: int) -> Optional[User]: ...

@component
@conditional(profiles=("prod",))
class PostgresUserRepository(UserRepository):
    def __init__(self, db: Database):
        self.db = db
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        return User(**row) if row else None

@component
@on_missing(UserRepository)
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self.users = {}
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

# application/services.py
@component
class UserService:
    def __init__(self, repo: UserRepository, bus: EventBus):
        self.repo = repo
        self.bus = bus
    
    @intercepted_by(AuditInterceptor)
    async def get_user(self, user_id: int) -> Optional[User]:
        user = self.repo.find_by_id(user_id)
        if user:
            await self.bus.publish(UserViewedEvent(user.id))
        return user

# presentation/api.py
@component
@scope("request")
class RequestContext:
    def __init__(self):
        self.user_id = extract_user_from_jwt()

@component
class UserController:
    def __init__(self, service: UserService, ctx: RequestContext):
        self.service = service
        self.ctx = ctx
    
    async def get_current_user(self) -> User:
        return await self.service.get_user(self.ctx.user_id)

# main.py
container = init(
    modules=["domain", "infrastructure", "application", "presentation"],
    profiles=("prod",),
    config=(EnvSource(),)
)

# Usage in a web framework (FastAPI example)
@app.get("/me")
async def me(request: Request):
    request_id = uuid.uuid4()
    with container.scope("request", request_id):
        controller = await container.aget(UserController)
        return await controller.get_current_user()
```
