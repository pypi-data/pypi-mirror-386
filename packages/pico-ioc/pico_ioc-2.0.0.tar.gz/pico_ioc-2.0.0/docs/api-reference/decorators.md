# Decorators Reference

This page provides a quick reference for all decorators provided by `pico-ioc`.

---

## **`@component(cls=None, *, name: Any = None)`**

Marks a class as a component to be managed by the container.

* **`name`**: (Optional) Assigns a specific **Key** (usually a string) to this component instead of using its class type. Useful for registering multiple components under a common name or interface.

---

## **`@factory(cls)`**

Marks a class as a factory for creating other components. Factory methods use `@provides`.

---

## **`@provides(key: Any)`**

Marks a method *inside* a `@factory` class as the provider for a specific **Key**.

* **`key`**: The **Key** (class type or string) that this method provides an instance for.

---

## **`@configuration(cls=None, *, prefix: Optional[str] = None)`**

Marks a `dataclass` as a configuration object to be populated from `ConfigSource`s (like `EnvSource`).

* **`prefix`**: (Optional) A prefix added to the dataclass field names when looking up values in the `ConfigSource` (e.g., `prefix="APP_"` looks for `APP_DEBUG` for a field named `DEBUG`).

---

## **`@configured(target: Any, *, prefix: Optional[str] = None)`**

Registers a provider that binds a nested configuration tree (from `TreeSource`s like `YamlTreeSource`) to a target `dataclass` or class graph.

* **`target`**: The root `dataclass` or class type to instantiate and populate.
* **`prefix`**: The top-level key in the configuration tree to map from (e.g., `"app"` for an `app:` section in YAML).

---

## **`@scope(name: str)`**

Sets the **Scope** (lifecycle) for a component.

* **`name`**: The name of the scope (e.g., `"singleton"`, `"prototype"`, `"request"`).

---

## **`@lazy(obj)`**

Marks a `singleton` component to be instantiated only when it's first requested (`get`/`aget`), not eagerly during `init()`.

---

## **`@primary(obj)`**

Marks a component as the default implementation when multiple components provide the same **Key** (usually an interface/protocol).

---

## **`@qualifier(*qs: Qualifier)`**

Applies one or more `Qualifier` tags to a component. Used for injecting specific lists of implementations.

* **`*qs`**: One or more instances of `Qualifier("tag_name")`.

---

## **`@conditional(*, profiles: Tuple[str, ...] = (), require_env: Tuple[str, ...] = (), predicate: Optional[Callable[[], bool]] = None)`**

Registers a component only if specific conditions are met. All specified conditions must be true.

* **`profiles`**: Registers only if one of these profile strings is active (passed to `init(profiles=...)`).
* **`require_env`**: Registers only if all these environment variables exist and are non-empty.
* **`predicate`**: Registers only if this callable returns `True`.

---

## **`@on_missing(selector: object, *, priority: int = 0)`**

Registers a component only if no other component is registered for the given `selector` (key or type) after the main binding phase. Acts as a fallback.

* **`selector`**: The **Key** or type to check for absence.
* **`priority`**: (Optional) If multiple `@on_missing` components target the same selector, the one with the higher priority wins.

---

## **`@configure(fn)`**

Marks a method on a component to be called immediately *after* the component instance is created and dependencies are injected (but before it's returned by `get`/`aget`). Can be `async def`.

---

## **`@cleanup(fn)`**

Marks a method on a component to be called when `container.cleanup_all()` or `container.cleanup_all_async()` is invoked. Used for releasing resources. Can be `async def`.

---

## **`@health(fn)`**

Marks a method on a component as a health check. These methods are executed by `container.health_check()`. The method should take no arguments (except `self`) and return a truthy value or raise an exception on failure.

---

## **`@intercepted_by(*interceptor_classes: type[MethodInterceptor])`**

Applies one or more AOP **Interceptors** to a method. The interceptors run before and after the original method call.

* **`*interceptor_classes`**: The class types of the `MethodInterceptor` components to apply.

---

## **`@subscribe(event_type: Type[Event], *, priority: int = 0, policy: ExecPolicy = ExecPolicy.INLINE, once: bool = False)`**

Marks a method (usually within an `AutoSubscriberMixin` class) to be called when an event of the specified type is published on the `EventBus`. Can be `async def`.

* **`event_type`**: The specific `Event` subclass to listen for.
* **`priority`**: (Optional) Handlers with higher priority run first.
* **`policy`**: (Optional) Controls execution (`INLINE`, `TASK`, `THREADPOOL`). See [Event Bus guide](../advanced-features/event-bus.md).
* **`once`**: (Optional) If `True`, the handler runs only once and is then automatically unsubscribed.

