# Integration: FastAPI

FastAPI has its own dependency injection system based on `Depends`. This system is excellent for web-layer dependencies (like request bodies, headers, and path parameters).

`pico-ioc` complements this by managing your deeper **application layer** (services, repositories, clients). You can easily integrate the two to get the best of both worlds: FastAPI handles the web, and `pico-ioc` handles your business logic.

This recipe shows how to:
1.  Initialize the `pico-ioc` container on application startup.
2.  Create a **request-scoped** container context for every incoming HTTP request.
3.  Inject your `pico-ioc`-managed services directly into your FastAPI routes using `Depends`.

---

## 1. Container Initialization (Lifespan)

First, we need to create our container. We'll create a global `PicoContainer` variable that will be initialized when FastAPI starts, using the `lifespan` event handler.

```python
# app.py
import uvicorn
import pico_ioc.event_bus
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pico_ioc import init, PicoContainer

# 1. Define your components in other modules
# (e.g., in 'services.py', 'database.py')

# 2. Create a global variable for the container
# It's 'None' for now.
container: PicoContainer | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the container's lifecycle.
    """
    global container
    print("Application starting... Initializing container.")
    
    # 3. Initialize the container
    container = init(
        modules=[
            "my_app.services", 
            "my_app.database",
            pico_ioc.event_bus # if you use it
        ],
        profiles=("prod",) # Set your profile
    )
    
    yield # The application is now running
    
    # 4. Clean up on shutdown
    print("Application shutting down... Cleaning up container.")
    await container.cleanup_all_async()
    container.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {"message": "Hello!"}

if __name__ == "__main__":
    uvicorn.run(app)
````

This gives us a single, application-wide `PicoContainer` instance.

-----

## 2\. Request Scope Middleware

To use `scope("request")` components, we need to tell `pico-ioc` when a request begins and ends. We do this by creating middleware.

This middleware will:

1.  Generate a unique ID for the request.
2.  Activate the `request` scope with that ID using `container.scope()`.
3.  Activate the container itself using `container.as_current()` so other functions can find it.

<!-- end list -->

```python
# app.py
import uuid
from fastapi import Request

# ... (previous setup code) ...

@app.middleware("http")
async def pico_scope_middleware(request: Request, call_next):
    """
    This middleware activates the 'request' scope
    and makes the container available for this request.
    """
    if not container:
        raise RuntimeError("Container not initialized")

    request_id = str(uuid.uuid4())
    
    # 1. Activate the request scope
    with container.scope("request", request_id):
        # 2. Make the container active for this context
        with container.as_current():
            try:
                # 3. Process the request
                response = await call_next(request)
                return response
            except Exception as e:
                # Handle exceptions
                return ...
```

-----

## 3\. Injecting Services into Routes

Now for the final piece: how do we get a service into our route? We can't just `Depends(UserService)`, because FastAPI doesn't know about `pico-ioc`.

We create a simple "bridge" function that lets `Depends` find the active `pico-ioc` container.

```python
# app.py
from fastapi import Depends
from typing import Type, Callable

# ... (previous setup code) ...

def get_current_container() -> PicoContainer:
    """
    A simple dependency to get the container
    that was activated by the middleware.
    """
    current = PicoContainer.get_current()
    if not current:
        raise RuntimeError("No active PicoContainer context!")
    return current

def get_service(service_type: Type[T]) -> Callable[..., T]:
    """
    This is the "bridge" function.
    It returns a *new* function that FastAPI can use as a dependency.
    """
    async def _dependency(
        container: PicoContainer = Depends(get_current_container)
    ) -> T:
        # Get the service from the active container
        return await container.aget(service_type)

    return _dependency

# --- Example Usage ---

# Assume you have this service defined in 'my_app.services'
@component
class MyService:
    def greet(self) -> str:
        return "Hello from MyService!"

# 4. Use the bridge in your route!
@app.get("/greet")
async def greet_user(
    service: MyService = Depends(get_service(MyService))
):
    """
    FastAPI will call get_service(MyService), which returns
    the _dependency function.
    
    FastAPI will then call _dependency, which gets the
    active container and .aget(MyService) from it.
    """
    return {"message": service.greet()}
```

This pattern gives you the full power of `pico-ioc`'s `aget()` resolution (including `async def __ainit__`, `@lazy`, etc.) inside your FastAPI routes, all while respecting the `request` scope.

-----

## Next Steps

This pattern can be adapted for other ASGI frameworks. Next, let's look at how to achieve a similar result with Flask, a popular WSGI framework.

  * **[Flask](./web-flask.md)**: Learn how to manage the container context using Flask's `g` object and request hooks.

