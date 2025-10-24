# Cookbook: Pattern: Security Checks with AOP (`@secured`)

**Goal:** Implement a declarative security mechanism where methods can be annotated with required roles or permissions (e.g., `@secured(roles=["admin"])`). An AOP interceptor checks the current user's privileges (from a request-scoped context) before method execution.

**Key `pico-ioc` Feature:** AOP (`MethodInterceptor`, `@intercepted_by`) combined with `@scope("request")` for contextual security checks. An alias (`@apply_security`) enhances readability.

## The Pattern

1.  **`@secured` Decorator:** Attaches required roles/permissions metadata to methods.
2.  **`SecurityContext`:** A `@component` with `@scope("request")` holding the current user's security info (populated by middleware).
3.  **`SecurityInterceptor`:** A `@component` implementing `MethodInterceptor`, injecting `SecurityContext` to perform checks based on `@secured` metadata. Raises `AuthorizationError` on failure.
4.  **`apply_security` Alias:** Defined as `intercepted_by(SecurityInterceptor)` for cleaner code.
5.  **Application:** Classes use `@apply_security`; methods use `@secured(...)`.
6.  **Bootstrap & Request Handling:** `init()` scans modules. Middleware manages the `request` scope and populates `SecurityContext`.

## Full, Runnable Example

### 1. Project Structure

```

.
├── security\_lib/
│   ├── **init**.py
│   ├── context.py     \<-- SecurityContext
│   ├── decorator.py   \<-- @secured and AuthorizationError
│   └── interceptor.py \<-- SecurityInterceptor & apply\_security alias
├── my\_app/
│   ├── **init**.py
│   └── services.py    \<-- Example service
└── main.py              \<-- Simulation entrypoint

```

### 2. Security Library (`security_lib/`)

#### Decorator & Exception (`decorator.py`)

```python
# security_lib/decorator.py
import functools
from typing import Callable, List, Optional

SECURED_META = "_pico_secured_meta" # Metadata key

class AuthorizationError(Exception):
    """Custom exception for failed security checks."""
    pass

def secured(*, roles: Optional[List[str]] = None, permissions: Optional[List[str]] = None):
    """Decorator to specify required roles or permissions for a method."""
    if not roles and not permissions:
        raise ValueError("Must specify either 'roles' or 'permissions' for @secured")
    metadata = {"roles": set(roles or []), "permissions": set(permissions or [])}

    def decorator(func: Callable) -> Callable:
        setattr(func, SECURED_META, metadata)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(wrapper, SECURED_META, metadata)
        return wrapper
    return decorator
```

#### Security Context (`context.py`)

```python
# security_lib/context.py
from dataclasses import dataclass, field
from typing import Set, List
from pico_ioc import component, scope

@component
@scope("request") # One instance per request
@dataclass
class SecurityContext:
    """Holds the current request's user security information."""
    user_id: str | None = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    is_authenticated: bool = False

    def load_from_request(self, user_id: str, roles: List[str], perms: List[str]):
        """Populates context (e.g., from middleware based on token/session)."""
        self.user_id = user_id
        self.roles = set(roles)
        self.permissions = set(perms)
        self.is_authenticated = True
        print(f"[Context] Loaded SecurityContext for user '{user_id}' with roles {self.roles}")
```

#### Interceptor & Alias (`interceptor.py`)

```python
# security_lib/interceptor.py
from typing import Any, Callable
from pico_ioc import component, MethodInterceptor, MethodCtx, intercepted_by
from .context import SecurityContext
from .decorator import SECURED_META, AuthorizationError

@component # <-- Interceptor is a component
class SecurityInterceptor(MethodInterceptor):
    def __init__(self, context: SecurityContext):
        # Inject the *current request's* SecurityContext
        self.context = context
        print("[Interceptor] SecurityInterceptor initialized.")

    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        try:
            # Access the original function for metadata
            original_func = getattr(ctx.cls, ctx.name)
            security_meta = getattr(original_func, SECURED_META, None)
        except AttributeError:
            security_meta = None

        if not security_meta:
            # Not a secured method, proceed
            return call_next(ctx)

        print(f"[Interceptor] Checking security for {ctx.cls.__name__}.{ctx.name}")

        # --- Authentication Check ---
        if not self.context.is_authenticated:
            raise AuthorizationError("User is not authenticated.")

        # --- Role Check ---
        required_roles = security_meta.get("roles", set())
        if required_roles and not required_roles.issubset(self.context.roles):
            raise AuthorizationError(
                f"User '{self.context.user_id}' lacks required roles: "
                f"{required_roles - self.context.roles}"
            )

        # --- Permission Check ---
        required_perms = security_meta.get("permissions", set())
        if required_perms and not required_perms.issubset(self.context.permissions):
             raise AuthorizationError(
                f"User '{self.context.user_id}' lacks required permissions: "
                f"{required_perms - self.context.permissions}"
            )

        # --- Check Passed ---
        print("[Interceptor] Security check PASSED.")
        return call_next(ctx)

# Define the alias for convenience and readability
apply_security = intercepted_by(SecurityInterceptor)
```

#### Library `__init__.py`

```python
# security_lib/__init__.py
from .decorator import secured, AuthorizationError
from .context import SecurityContext
from .interceptor import SecurityInterceptor, apply_security # Export the alias

__all__ = [
    "secured", "AuthorizationError",
    "SecurityContext", "SecurityInterceptor", "apply_security" # Include alias
]
```

### 3\. Application Code (`my_app/services.py`)

Apply the `@secured` decorator to methods and the `@apply_security` alias to the class.

```python
# my_app/services.py
from pico_ioc import component
from security_lib import secured, apply_security # Import the alias and @secured

@component
@apply_security # <-- Use the alias at the class level
class AdminService:

    @secured(roles=["admin"]) # <-- Define requirements for this method
    def perform_admin_action(self, action: str):
        print(f"[AdminService] Performing critical admin action: {action}")
        return f"Admin action '{action}' completed."

    @secured(permissions=["read_data"]) # <-- Different requirements here
    def view_sensitive_data(self) -> dict:
        print("[AdminService] Accessing sensitive data...")
        return {"data": "secret_info"}

    # No @secured decorator
    def get_public_info(self) -> str:
        # The interceptor runs (due to @apply_security on the class),
        # finds no @secured metadata, and proceeds directly.
        print("[AdminService] Getting public info...")
        return "Public information"
```

### 4\. Main Application (`main.py`)

The simulation remains the same, activating scopes and populating the context.

```python
# main.py
import uuid
import time # Added for clarity
from pico_ioc import init, PicoContainer
from my_app.services import AdminService
from security_lib import SecurityContext, AuthorizationError

def run_simulation():
    print("--- Initializing Container ---")
    # Scan app and security library
    container = init(modules=["my_app", "security_lib"])
    print("--- Container Initialized ---\n")

    # --- Simulate Request 1: Admin User ---
    print("--- SIMULATING REQUEST 1: ADMIN USER ---")
    request_id_1 = f"req-{uuid.uuid4().hex[:6]}"
    with container.scope("request", request_id_1):
        # Populate context for this "request"
        sec_ctx = container.get(SecurityContext)
        sec_ctx.load_from_request(user_id="admin_user", roles=["admin", "user"], perms=["read_data"])

        # Get the service (interceptor gets correct context)
        admin_service = container.get(AdminService)

        try:
            print(f"\nCalling perform_admin_action...")
            result = admin_service.perform_admin_action("restart_server")
            print(f"Result: {result}")

            time.sleep(0.1) # Small delay for output clarity
            print(f"\nCalling view_sensitive_data...")
            data = admin_service.view_sensitive_data()
            print(f"Result: {data}")

            time.sleep(0.1)
            print(f"\nCalling get_public_info...")
            info = admin_service.get_public_info()
            print(f"Result: {info}")

        except AuthorizationError as e:
            print(f"Authorization Error: {e}")
    print("-" * 40) # Separator


    # --- Simulate Request 2: Regular User ---
    print("\n--- SIMULATING REQUEST 2: REGULAR USER ---")
    request_id_2 = f"req-{uuid.uuid4().hex[:6]}"
    with container.scope("request", request_id_2):
        sec_ctx = container.get(SecurityContext)
        # This user only has the 'user' role and 'read_data' permission
        sec_ctx.load_from_request(user_id="normal_user", roles=["user"], perms=["read_data"])

        admin_service = container.get(AdminService)

        try:
            print(f"\nCalling perform_admin_action...")
            result = admin_service.perform_admin_action("delete_user") # Should fail
            print(f"Result: {result}")
        except AuthorizationError as e:
            print(f"Caught Expected Error: {e}")

        time.sleep(0.1)
        try:
            print(f"\nCalling view_sensitive_data...")
            data = admin_service.view_sensitive_data() # Should pass
            print(f"Result: {data}")
        except AuthorizationError as e:
            print(f"Authorization Error: {e}")
    print("-" * 40)


    # --- Simulate Request 3: Unauthenticated ---
    print("\n--- SIMULATING REQUEST 3: UNAUTHENTICATED USER ---")
    request_id_3 = f"req-{uuid.uuid4().hex[:6]}"
    with container.scope("request", request_id_3):
        # SecurityContext is created but not populated (is_authenticated=False)
        admin_service = container.get(AdminService)
        try:
            print(f"\nCalling view_sensitive_data...")
            data = admin_service.view_sensitive_data() # Should fail
            print(f"Result: {data}")
        except AuthorizationError as e:
            print(f"Caught Expected Error: {e}")
    print("-" * 40)

if __name__ == "__main__":
    run_simulation()
```

## 5\. Benefits

  * **Declarative Security:** Permissions clearly stated via `@secured`.
  * **Clean Business Logic:** Service methods remain focused.
  * **Centralized Logic:** Security checks handled by `SecurityInterceptor`.
  * **Readability:** The `@apply_security` alias makes the intent clear at the class level.
  * **Testable:** Services and the interceptor can be tested independently.
  * **Flexible:** Easily extend `@secured` and the interceptor for more complex rules.

