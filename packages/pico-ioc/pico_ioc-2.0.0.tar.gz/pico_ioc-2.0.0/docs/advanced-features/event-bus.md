# Advanced: The Event Bus

As your application grows, services often become tightly coupled.

**Problem:** Your `UserService` needs to know about many other services. When a user is created, it must *directly* call all of them:

```python
@component
class UserService:
    def __init__(
        self, 
        db: Database,
        email_service: EmailService,
        analytics: AnalyticsService,
        audit_log: AuditLogService
    ):
        self.db = db
        self.email_service = email_service
        self.analytics = analytics
        self.audit_log = audit_log

    async def create_user(self, email: str):
        # 1. Business Logic
        user = self.db.save(email)
        
        # 2. Tightly Coupled Calls
        # What if EmailService fails?
        # What if we add a new service? We have to edit this file.
        await self.email_service.send_welcome_email(user)
        await self.analytics.track_event("user_created", user.id)
        await self.audit_log.record(f"User {user.id} created")
        
        return user
````

This is brittle and hard to maintain. `UserService` shouldn't have to know about all these other concerns.

**Solution:** `pico-ioc` provides a built-in **asynchronous event bus**. This allows you to *decouple* your services using a **Publish/Subscribe** pattern.

Instead of calling other services, `UserService` simply publishes an `Event`. Other services can then "subscribe" to that event and react to it independently.

-----

## 1\. The Core Concepts

### `Event`

An `Event` is a simple class (like a `dataclass`) that holds information about what happened.

```python
from dataclasses import dataclass
from pico_ioc import Event

@dataclass
class UserCreatedEvent(Event):
    user_id: int
    email: str
```

### `EventBus`

The `EventBus` is a component provided by `pico-ioc` that you can inject. It has two key methods:

  * `await bus.publish(event)`: Publishes an event and waits for all subscribers to finish.
  * `bus.post(event)`: (Advanced) Puts an event on a background queue to be processed later.

### `subscribe`

The `@subscribe` decorator allows a method to "listen" for a specific event type.

-----

## 2\. Step-by-Step Example

Let's refactor our `UserService` to use the event bus.

### Step 1: Define the Event

First, we define the event that will be published.

```python
# events.py
from dataclasses import dataclass
from pico_ioc import Event

@dataclass
class UserCreatedEvent(Event):
    user_id: int
    email: str
```

### Step 2: Refactor `UserService` to *Publish*

Now, `UserService` only needs to know about the `EventBus`. Its dependencies are drastically reduced.

```python
# services/user_service.py
from pico_ioc import component, EventBus
from .events import UserCreatedEvent

@component
class UserService:
    def __init__(self, db: Database, bus: EventBus):
        self.db = db
        self.bus = bus # Just inject the bus

    async def create_user(self, email: str):
        # 1. Business Logic
        user = self.db.save(email)
        
        # 2. Publish Event
        # We just shout "this happened!" and don't care who is listening.
        event = UserCreatedEvent(user_id=user.id, email=user.email)
        await self.bus.publish(event)
        
        return user
```

**Important:** `UserService` is now completely decoupled from the email, analytics, and audit services.

### Step 3: Create Subscribers

Next, we create our "listener" components. We use the `AutoSubscriberMixin` to automatically find and register `@subscribe` methods.

```python
# services/email_service.py
from pico_ioc import component, subscribe
from pico_ioc.event_bus import AutoSubscriberMixin
from .events import UserCreatedEvent

@component
class EmailService(AutoSubscriberMixin):
    
    @subscribe(UserCreatedEvent)
    async def on_user_created(self, event: UserCreatedEvent):
        # This method is automatically called when UserCreatedEvent is published
        print(f"EMAIL: Sending welcome email to {event.email}")
        await self.send_email(event.email, "Welcome!")

    async def send_email(self, to, body): ...
```

```python
# services/analytics_service.py
from pico_ioc import component, subscribe
from pico_ioc.event_bus import AutoSubscriberMixin
from .events import UserCreatedEvent

@component
class AnalyticsService(AutoSubscriberMixin):
    
    @subscribe(UserCreatedEvent, policy=ExecPolicy.TASK)
    async def on_user_created(self, event: UserCreatedEvent):
        # This handler is non-critical, so we run it as a
        # "fire and forget" task that doesn't block the publisher.
        print(f"ANALYTICS: Tracking event for user {event.user_id}")
        await self.track(event.user_id)

    async def track(self, user_id): ...
```

### Step 4: Run It

You must include `pico_ioc.event_bus` in your `init()` call to register the `EventBus` component itself.

```python
# main.py
import pico_ioc.event_bus
from pico_ioc import init
from services.user_service import UserService

container = init(
    modules=[
        "events",
        "services.user_service",
        "services.email_service",
        "services.analytics_service",
        pico_ioc.event_bus # Don't forget this!
    ]
)

async def main():
    user_service = await container.aget(UserService)
    await user_service.create_user("alice@example.com")
    
    # ...
    await container.cleanup_all_async()

# Output:
# EMAIL: Sending welcome email to alice@example.com
# ANALYTICS: Tracking event for user 1
```

-----

## 3\. Execution Policies (`ExecPolicy`)

By default, `await bus.publish(event)` **waits for all subscribers to complete**.

You can control this behavior using the `policy` argument in `@subscribe`:

  * `ExecPolicy.INLINE` (Default): The publisher `await`s this handler. Use this for critical, blocking tasks (like sending the email).
  * `ExecPolicy.TASK`: The bus starts this handler as a "fire and forget" `asyncio.Task` and **does not** wait for it to complete. Use this for non-critical tasks (like analytics or logging).
  * `ExecPolicy.THREADPOOL`: For **sync** (non-async) handlers. Runs the handler in a separate thread so it doesn't block the async event loop.

-----

## 4\. `publish()` vs. `post()`

| Method | `await bus.publish(event)` | `bus.post(event)` |
| :--- | :--- | :--- |
| **Execution** | **Synchronous (in-process)** | **Asynchronous (queued)** |
| **How it works** | Immediately finds and `await`s all `INLINE` subscribers. | Puts the event on a background queue. A separate "worker" (if started) processes the queue later. |
| **Use Case** | 99% of the time. You want the event handled *now*. | Advanced "fire and forget" from a sync context, or when you need a durable queue (with `max_queue_size`). |

**Rule of Thumb:** Always use `await bus.publish()` unless you have a specific reason to use the background queue.

-----

## Next Steps

You've seen how to decouple services. The next guide covers how to control *which* services are even registered in the first place, based on your environment.

  * **[Conditional Binding](./conditional-binding.md)**: Learn how to use `@primary`, `@on_missing`, and `@conditional` to control your container's setup.

