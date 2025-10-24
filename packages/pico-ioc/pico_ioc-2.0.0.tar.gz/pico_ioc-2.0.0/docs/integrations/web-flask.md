# Integration: Flask

Flask is a classic, flexible WSGI framework. It doesn't have a built-in dependency injection system, which makes `pico-ioc` a perfect partner for managing your application's service layer.

This guide shows the standard pattern for integrating the two:
1.  Initialize the `pico-ioc` container when the Flask `app` is created.
2.  Use Flask's `before_request` hook to activate the `request` scope and the container.
3.  Use Flask's `teardown_request` hook to clean up the scopes.
4.  Access your services from within your Flask views.

---

## 1. Container Initialization

The simplest pattern is to create your Flask `app` and your `pico-ioc` `container` in the same factory function. This allows you to register the container with the app's hooks.

```python
# app.py
from flask import Flask
from pico_ioc import init, PicoContainer

# 1. Define your components in other modules
# (e.g., in 'services.py', 'database.py')

def create_app() -> Flask:
    app = Flask(__name__)
    
    # 2. Initialize the pico-ioc container
    container = init(
        modules=[
            "my_app.services", 
            "my_app.database"
        ],
        profiles=("prod",) # Set your profile
    )
    
    # 3. "Attach" the container to the app for hooks
    register_pico_hooks(app, container)
    
    # 4. Register your Flask routes
    @app.route("/")
    def home():
        return "Hello from Flask!"

    return app

def register_pico_hooks(app: Flask, container: PicoContainer):
    # We will define these hooks in the next step
    pass

app = create_app()

if __name__ == "__main__":
    app.run()
````

-----

## 2\. Request Scope Management (The Hooks)

To make `scope("request")` work, we need to tell `pico-ioc` when a request starts and stops. Flask's `@app.before_request` and `@app.teardown_request` hooks are perfect for this.

We will use these hooks to activate the container and the scope, and then clean them up afterward.

```python
# app.py
import uuid
import contextvars
from flask import Flask
from pico_ioc import init, PicoContainer

# We need to store the context tokens to reset them later
_pico_container_token: contextvars.Token | None = None
_pico_request_scope_token: contextvars.Token | None = None


def register_pico_hooks(app: Flask, container: PicoContainer):
    
    @app.before_request
    def _pico_activate():
        """
        Before each request, activate the container and
        the 'request' scope.
        """
        global _pico_container_token, _pico_request_scope_token
        
        request_id = str(uuid.uuid4())
        
        # 1. Activate the request scope
        _pico_request_scope_token = container.activate_scope(
            "request", request_id
        )
        # 2. Activate the container itself
        _pico_container_token = container.activate()

    @app.teardown_request
    def _pico_deactivate(exception=None):
        """
        After each request, deactivate everything
        in reverse order.
        """
        global _pico_container_token, _pico_request_scope_token
        
        # 1. Deactivate the container
        if _pico_container_token:
            container.deactivate(_pico_container_token)
            _pico_container_token = None
            
        # 2. Deactivate the request scope
        if _pico_request_scope_token:
            container.deactivate_scope("request", _pico_request_scope_token)
            _pico_request_scope_token = None

# ... (the create_app function from before) ...
```

This code ensures that for every request, a unique `request` scope is active, and `PicoContainer.get_current()` will work.

-----

## 3\. Injecting Services into Routes (Views)

Unlike FastAPI, Flask doesn't have a per-route DI system. Instead, you access the **currently active container** (which we set in the middleware) and manually `get` your service.

`PicoContainer.get_current()` is the key.

```python
# services.py
from pico_ioc import component, scope

@component
@scope("request")
class RequestData:
    """A component that is unique for each request."""
    def __init__(self):
        # We can get the active scope ID
        self.scope_id = PicoContainer.get_current().scopes.get_id("request")
        print(f"RequestData created for {self.scope_id}")

@component
class MyService:
    def __init__(self, data: RequestData):
        self.data = data
        
    def greet(self) -> str:
        return f"Hello from MyService! Your request ID is {self.data.scope_id}"

# app.py
# ... (all the setup code from above) ...

def register_routes(app: Flask):
    @app.route("/")
    def home():
        return "Hello from Flask!"

    @app.route("/greet")
    def greet_user():
        """
        This is the "injection" pattern for Flask.
        """
        # 1. Get the container that was activated
        #    by the 'before_request' hook.
        container = PicoContainer.get_current()
        if not container:
            return "Error: Container not found", 500
        
        # 2. 'get' your service. 'pico-ioc' will handle
        #    resolving all dependencies, including the
        #    request-scoped 'RequestData'.
        service = container.get(MyService)
        
        return service.greet()

def create_app() -> Flask:
    app = Flask(__name__)
    container = init(modules=["services"])
    
    register_pico_hooks(app, container)
    register_routes(app) # Register our new routes
    
    return app

app = create_app()
```

When you visit `/greet`, the `before_request` hook runs, `container.get(MyService)` resolves the `request` scope correctly, and you get a response.

-----

## Next Steps

This pattern is common for WSGI frameworks. Let's now look at how to integrate `pico-ioc` with a more monolithic framework, Django.

  * **[Django](./web-django.md)**: Learn how to initialize the container and use it for a "service layer" alongside the Django ORM.

