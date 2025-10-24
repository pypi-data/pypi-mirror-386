# src/pico_ioc/container.py
import inspect
import contextvars
from typing import Any, Dict, List, Optional, Tuple, overload, Union
from contextlib import contextmanager
from .constants import LOGGER, PICO_META
from .exceptions import CircularDependencyError, ComponentCreationError, ProviderNotFoundError
from .factory import ComponentFactory
from .locator import ComponentLocator
from .scope import ScopedCaches, ScopeManager
from .aop import UnifiedComponentProxy, ContainerObserver

KeyT = Union[str, type]
_resolve_chain: contextvars.ContextVar[Tuple[KeyT, ...]] = contextvars.ContextVar("pico_resolve_chain", default=())

class PicoContainer:
    _container_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("pico_container_id", default=None)
    _container_registry: Dict[str, "PicoContainer"] = {}

    class _Ctx:
        def __init__(self, container_id: str, profiles: Tuple[str, ...], created_at: float) -> None:
            self.container_id = container_id
            self.profiles = profiles
            self.created_at = created_at
            self.resolve_count = 0
            self.cache_hit_count = 0

    def __init__(self, component_factory: ComponentFactory, caches: ScopedCaches, scopes: ScopeManager, observers: Optional[List["ContainerObserver"]] = None, container_id: Optional[str] = None, profiles: Tuple[str, ...] = ()) -> None:
        self._factory = component_factory
        self._caches = caches
        self.scopes = scopes
        self._locator: Optional[ComponentLocator] = None
        self._observers = list(observers or [])
        self.container_id = container_id or self._generate_container_id()
        import time as _t
        self.context = PicoContainer._Ctx(container_id=self.container_id, profiles=profiles, created_at=_t.time())
        PicoContainer._container_registry[self.container_id] = self

    @staticmethod
    def _generate_container_id() -> str:
        import time as _t, random as _r
        return f"c{_t.time_ns():x}{_r.randrange(1<<16):04x}"

    @classmethod
    def get_current(cls) -> Optional["PicoContainer"]:
        cid = cls._container_id_var.get()
        return cls._container_registry.get(cid) if cid else None

    @classmethod
    def get_current_id(cls) -> Optional[str]:
        return cls._container_id_var.get()

    @classmethod
    def all_containers(cls) -> Dict[str, "PicoContainer"]:
        return dict(cls._container_registry)

    def activate(self) -> contextvars.Token:
        return PicoContainer._container_id_var.set(self.container_id)

    def deactivate(self, token: contextvars.Token) -> None:
        PicoContainer._container_id_var.reset(token)

    @contextmanager
    def as_current(self):
        token = self.activate()
        try:
            yield self
        finally:
            self.deactivate(token)

    def attach_locator(self, locator: ComponentLocator) -> None:
        self._locator = locator

    def _cache_for(self, key: KeyT):
        md = self._locator._metadata.get(key) if self._locator else None
        sc = (md.scope if md else "singleton")
        return self._caches.for_scope(self.scopes, sc)

    def has(self, key: KeyT) -> bool:
        cache = self._cache_for(key)
        return cache.get(key) is not None or self._factory.has(key)

    @overload
    def get(self, key: type) -> Any: ...
    @overload
    def get(self, key: str) -> Any: ...
    def get(self, key: KeyT) -> Any:
        cache = self._cache_for(key)
        cached = cache.get(key)
        if cached is not None:
            self.context.cache_hit_count += 1
            for o in self._observers: o.on_cache_hit(key)
            return cached
        import time as _tm
        t0 = _tm.perf_counter()
        chain = list(_resolve_chain.get())
        for k in chain:
            if k == key:
                raise CircularDependencyError(chain, key)
        token_chain = _resolve_chain.set(tuple(chain + [key]))
        token_container = self.activate()
        try:
            if not self._factory.has(key):
                alt = None
                if isinstance(key, type):
                    alt = self._resolve_type_key(key)
                elif isinstance(key, str) and self._locator:
                    for k, md in self._locator._metadata.items():
                        if md.pico_name == key:
                            alt = k
                            break
                if alt is not None:
                    self._factory.bind(key, lambda a=alt: self.get(a))
            provider = self._factory.get(key)
            try:
                instance = provider()
            except ProviderNotFoundError as e:
                raise
            except Exception as e:
                raise ComponentCreationError(key, e)
            instance = self._maybe_wrap_with_aspects(key, instance)
            cache.put(key, instance)
            self.context.resolve_count += 1
            took_ms = (_tm.perf_counter() - t0) * 1000
            for o in self._observers: o.on_resolve(key, took_ms)
            return instance
        finally:
            _resolve_chain.reset(token_chain)
            self.deactivate(token_container)

    async def aget(self, key: KeyT) -> Any:
        cache = self._cache_for(key)
        cached = cache.get(key)
        if cached is not None:
            self.context.cache_hit_count += 1
            for o in self._observers: o.on_cache_hit(key)
            return cached
        import time as _tm
        t0 = _tm.perf_counter()
        chain = list(_resolve_chain.get())
        for k in chain:
            if k == key:
                raise CircularDependencyError(chain, key)
        token_chain = _resolve_chain.set(tuple(chain + [key]))
        token_container = self.activate()
        try:
            if not self._factory.has(key):
                alt = None
                if isinstance(key, type):
                    alt = self._resolve_type_key(key)
                elif isinstance(key, str) and self._locator:
                    for k, md in self._locator._metadata.items():
                        if md.pico_name == key:
                            alt = k
                            break
                if alt is not None:
                    self._factory.bind(key, lambda a=alt: self.get(a))
            provider = self._factory.get(key)
            try:
                instance = provider()
                if inspect.isawaitable(instance):
                    instance = await instance
            except ProviderNotFoundError as e:
                raise
            except Exception as e:
                raise ComponentCreationError(key, e)
            instance = self._maybe_wrap_with_aspects(key, instance)
            cache.put(key, instance)
            self.context.resolve_count += 1
            took_ms = (_tm.perf_counter() - t0) * 1000
            for o in self._observers: o.on_resolve(key, took_ms)
            return instance
        finally:
            _resolve_chain.reset(token_chain)
            self.deactivate(token_container)

    def _resolve_type_key(self, key: type):
        if not self._locator:
            return None
        cands: List[Tuple[bool, Any]] = []
        for k, md in self._locator._metadata.items():
            typ = md.provided_type or md.concrete_class
            if not isinstance(typ, type):
                continue
            try:
                if typ is not key and issubclass(typ, key):
                    cands.append((md.primary, k))
            except Exception:
                continue
        if not cands:
            return None
        prim = [k for is_p, k in cands if is_p]
        return prim[0] if prim else cands[0][1]

    def _maybe_wrap_with_aspects(self, key, instance: Any) -> Any:
        if isinstance(instance, UnifiedComponentProxy):
            return instance
        cls = type(instance)
        for _, fn in inspect.getmembers(cls, predicate=lambda m: inspect.isfunction(m) or inspect.ismethod(m) or inspect.iscoroutinefunction(m)):
            if getattr(fn, "_pico_interceptors_", None):
                return UnifiedComponentProxy(container=self, target=instance)
        return instance

    def cleanup_all(self) -> None:
        for _, obj in self._caches.all_items():
            for _, m in inspect.getmembers(obj, predicate=inspect.ismethod):
                meta = getattr(m, PICO_META, {})
                if meta.get("cleanup", False):
                    from .api import _resolve_args
                    kwargs = _resolve_args(m, self)
                    m(**kwargs)
        if self._locator:
            seen = set()
            for md in self._locator._metadata.values():
                fc = md.factory_class
                if fc and fc not in seen:
                    seen.add(fc)
                    inst = self.get(fc) if self._factory.has(fc) else fc()
                    for _, m in inspect.getmembers(inst, predicate=inspect.ismethod):
                        meta = getattr(m, PICO_META, {})
                        if meta.get("cleanup", False):
                            from .api import _resolve_args
                            kwargs = _resolve_args(m, self)
                            m(**kwargs)

    def activate_scope(self, name: str, scope_id: Any):
        return self.scopes.activate(name, scope_id)

    def deactivate_scope(self, name: str, token: Optional[contextvars.Token]) -> None:
        self.scopes.deactivate(name, token)

    def info(self, msg: str) -> None:
        LOGGER.info(f"[{self.container_id[:8]}] {msg}")

    @contextmanager
    def scope(self, name: str, scope_id: Any):
        tok = self.activate_scope(name, scope_id)
        try:
            yield self
        finally:
            self.deactivate_scope(name, tok)

    def health_check(self) -> Dict[str, bool]:
        out: Dict[str, bool] = {}
        for k, obj in self._caches.all_items():
            for name, m in inspect.getmembers(obj, predicate=callable):
                if getattr(m, PICO_META, {}).get("health_check", False):
                    try:
                        out[f"{getattr(k,'__name__',k)}.{name}"] = bool(m())
                    except Exception:
                        out[f"{getattr(k,'__name__',k)}.{name}"] = False
        return out

    async def cleanup_all_async(self) -> None:
        for _, obj in self._caches.all_items():
            for _, m in inspect.getmembers(obj, predicate=inspect.ismethod):
                meta = getattr(m, PICO_META, {})
                if meta.get("cleanup", False):
                    from .api import _resolve_args
                    res = m(**_resolve_args(m, self))
                    import inspect as _i
                    if _i.isawaitable(res):
                        await res
        if self._locator:
            seen = set()
            for md in self._locator._metadata.values():
                fc = md.factory_class
                if fc and fc not in seen:
                    seen.add(fc)
                    inst = self.get(fc) if self._factory.has(fc) else fc()
                    for _, m in inspect.getmembers(inst, predicate=inspect.ismethod):
                        meta = getattr(m, PICO_META, {})
                        if meta.get("cleanup", False):
                            from .api import _resolve_args
                            res = m(**_resolve_args(m, self))
                            import inspect as _i
                            if _i.isawaitable(res):
                                await res
        try:
            from .event_bus import EventBus
            for _, obj in self._caches.all_items():
                if isinstance(obj, EventBus):
                    await obj.aclose()
        except Exception:
            pass

    def stats(self) -> Dict[str, Any]:
        import time as _t
        resolves = self.context.resolve_count
        hits = self.context.cache_hit_count
        total = resolves + hits
        return {
            "container_id": self.container_id,
            "profiles": self.context.profiles,
            "uptime_seconds": _t.time() - self.context.created_at,
            "total_resolves": resolves,
            "cache_hits": hits,
            "cache_hit_rate": (hits / total) if total > 0 else 0.0,
            "registered_components": len(self._locator._metadata) if self._locator else 0,
        }

    def shutdown(self) -> None:
        self.cleanup_all()
        PicoContainer._container_registry.pop(self.container_id, None)

