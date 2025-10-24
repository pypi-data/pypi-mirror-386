import pytest
import os
import types
import asyncio
import pickle
import logging
from dataclasses import dataclass
from typing import List, Any, Callable, Optional
import pico_ioc.event_bus
from pico_ioc import (
    init, component, factory, provides, configuration, conditional, scope,
    cleanup, configure, health, intercepted_by, lazy,
    PicoContainer, MethodInterceptor, MethodCtx, ScopeError,
    InvalidBindingError, CircularDependencyError, ComponentCreationError,
    ProviderNotFoundError, ConfigurationError, SerializationError,
    Event, subscribe, AutoSubscriberMixin, EventBus, EventBusClosedError
)


log_capture = []

class ListLogHandler(logging.Handler):
    def emit(self, record):
        log_capture.append(self.format(record))


test_logger = logging.getLogger("TestCoverageLogger")
test_logger.handlers.clear()
test_logger.addHandler(ListLogHandler())
test_logger.setLevel(logging.INFO)

@pytest.fixture(autouse=True)
def reset_logging_capture():
    log_capture.clear()

@component
class MissingDependency:
    pass

@component
class NeedsMissingComponent:
    def __init__(self, missing: MissingDependency):
        self.missing = missing

@component
class CircularA:
    def __init__(self, b: "CircularB"):
        self.b = b

@component
class CircularB:
    def __init__(self, a: CircularA):
        self.a = a

@component
class FailingComponent:
    def __init__(self):
        raise ValueError("Creation failure")

@configuration
@dataclass
class RequiredConfig:
    REQUIRED_KEY: str

class Widget:
    pass

@factory
class WidgetFactory:
    @provides(Widget)
    def build_widget(self) -> Widget:
        test_logger.info("Widget_Factory: Creating Widget")
        return Widget()

@component
class ConfiguredComponent:
    def __init__(self):
        self.configured = False
        self.widget = None
        test_logger.info("ConfiguredComponent: __init__")
    
    @configure
    def setup(self, widget: Widget):
        self.widget = widget
        self.configured = True
        test_logger.info("ConfiguredComponent: @configure called")

@component
class AsyncResource:
    def __init__(self):
        self.closed = False
        test_logger.info("AsyncResource: Created")
    
    @cleanup
    async def async_close(self):
        await asyncio.sleep(0)
        self.closed = True
        test_logger.info("AsyncResource: @cleanup async called")

@component
@conditional(require_env=("MY_TEST_VAR",))
class EnvConditionalComponent:
    pass

def check_predicate():
    return os.environ.get("PREDICATE_SWITCH") == "ON"

@component
@conditional(predicate=check_predicate)
class PredicateConditionalComponent:
    pass

@component
class HealthyComponent:
    @health
    def check_db(self):
        test_logger.info("Health: check_db OK")
        return True

    @health
    def check_api(self):
        test_logger.info("Health: check_api FAILED")
        raise ValueError("API not available")

@component
class AuditInterceptor(MethodInterceptor):
    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        test_logger.info(f"AUDIT_ASYNC - Entering: {ctx.name}")
        res = call_next(ctx)
        test_logger.info(f"AUDIT_ASYNC - Exiting: {ctx.name}")
        return res

@component
class AsyncAuditedService:
    @intercepted_by(AuditInterceptor)
    async def do_async_work(self, val: int) -> int:
        test_logger.info("AsyncAuditedService: working...")
        await asyncio.sleep(0)
        return val * 2

@component
@lazy
class MyLazyComponentForPickle:
    def __init__(self):
        self.value = 42

class MyTestEvent(Event):
    def __init__(self, msg: str):
        self.msg = msg

@component
class MyTestSubscriber(AutoSubscriberMixin):
    def __init__(self):
        self.received: List[str] = []

    @subscribe(MyTestEvent)
    def handle_event(self, evt: MyTestEvent):
        test_logger.info(f"Event received: {evt.msg}")
        self.received.append(evt.msg)


test_module = types.ModuleType("test_coverage_module")
all_definitions = [
    NeedsMissingComponent, MissingDependency, CircularA, CircularB, FailingComponent,
    RequiredConfig, Widget, WidgetFactory, ConfiguredComponent, AsyncResource,
    EnvConditionalComponent, PredicateConditionalComponent, HealthyComponent,
    AuditInterceptor, AsyncAuditedService, MyLazyComponentForPickle,
    MyTestEvent, MyTestSubscriber
]
for item in all_definitions:
    if hasattr(item, "__name__"):
        setattr(test_module, item.__name__, item)


def test_invalid_binding_error_on_init():
    mod = types.ModuleType("fail_mod")
    setattr(mod, NeedsMissingComponent.__name__, NeedsMissingComponent)
    
    with pytest.raises(InvalidBindingError) as e:
        init(mod, validate_only=True)
    
    assert "NeedsMissingComponent constructor depends on MissingDependency" in str(e.value)

def test_circular_dependency_error():
    container = init(test_module)
    with pytest.raises(ComponentCreationError) as e:
        container.get(CircularA)
    
    root_cause = e.value
    while hasattr(root_cause, 'cause') and root_cause.cause is not None:
            root_cause = root_cause.cause
    
    assert isinstance(root_cause, CircularDependencyError)
    assert "CircularA" in str(e.value)

def test_component_creation_error():
    container = init(test_module)
    with pytest.raises(ComponentCreationError) as e:
        container.get(FailingComponent)
    
    assert "Failed to create component for key: FailingComponent" in str(e.value)
    assert "ValueError: Creation failure" in str(e.value)

def test_provider_not_found_error():
    container = init(types.ModuleType("empty_mod"))
    
    with pytest.raises(ProviderNotFoundError) as e_str:
        container.get("non_existent_key")
    assert "Provider not found for key: non_existent_key" in str(e_str.value)

    class NonExistentClass: pass
    with pytest.raises(ProviderNotFoundError) as e_type:
        container.get(NonExistentClass)
    assert "Provider not found for key: NonExistentClass" in str(e_type.value)

def test_configuration_error_missing_value():
    config_module = types.ModuleType("config_test_mod")
    setattr(config_module, RequiredConfig.__name__, RequiredConfig)
    
    with pytest.raises(ComponentCreationError) as e:
        container = init(config_module, config=())
        container.get(RequiredConfig) 
    
    assert isinstance(e.value.cause, ConfigurationError)
    assert "Missing configuration key: REQUIRED_KEY" in str(e.value.cause)

def test_configuration_error_disallowed_profile():
    with pytest.raises(ConfigurationError) as e:
        init(
            types.ModuleType("empty_mod"),
            profiles=("dev",),
            allowed_profiles=("prod", "test")
        )
    assert "Unknown profiles: ['dev']; allowed: ['prod', 'test']" in str(e.value)

def test_scope_error_unknown_scope():
    container = init(types.ModuleType("empty_mod"))
    with pytest.raises(ScopeError) as e:
        container.activate_scope("unreal_scope", "id-123")
    assert "Unknown scope: unreal_scope" in str(e.value)


def test_factory_and_provides_pattern():
    container = init(test_module)
    widget_instance = container.get(Widget)
    
    assert isinstance(widget_instance, Widget)
    assert "Widget_Factory: Creating Widget" in log_capture

def test_configure_lifecycle_method():
    container = init(test_module)
    
    assert "ConfiguredComponent: __init__" not in log_capture
    
    instance = container.get(ConfiguredComponent)
    
    assert instance.configured is True
    assert isinstance(instance.widget, Widget)
    
    init_index = log_capture.index("ConfiguredComponent: __init__")
    configure_index = log_capture.index("ConfiguredComponent: @configure called")
    assert init_index < configure_index

@pytest.mark.asyncio
async def test_async_cleanup_method():
    container = init(test_module)
    resource = container.get(AsyncResource)
    
    assert resource.closed is False
    assert "AsyncResource: Created" in log_capture
    
    await container.cleanup_all_async()
    
    assert resource.closed is True
    assert "AsyncResource: @cleanup async called" in log_capture


def test_conditional_on_env(monkeypatch):
    monkeypatch.delenv("MY_TEST_VAR", raising=False)
    container_no_env = init(test_module)
    with pytest.raises(ProviderNotFoundError):
        container_no_env.get(EnvConditionalComponent)
        
    monkeypatch.setenv("MY_TEST_VAR", "any_value")
    container_with_env = init(test_module)
    instance = container_with_env.get(EnvConditionalComponent)
    assert isinstance(instance, EnvConditionalComponent)

def test_conditional_on_predicate(monkeypatch):
    monkeypatch.setenv("PREDICATE_SWITCH", "OFF")
    container_false = init(test_module)
    with pytest.raises(ProviderNotFoundError):
        container_false.get(PredicateConditionalComponent)
        
    monkeypatch.setenv("PREDICATE_SWITCH", "ON")
    container_true = init(test_module)
    instance = container_true.get(PredicateConditionalComponent)
    assert isinstance(instance, PredicateConditionalComponent)

def test_health_check_decorator():
    container = init(test_module)
    
    container.get(HealthyComponent)
    
    health_status = container.health_check()
    
    assert "HealthyComponent.check_db" in health_status
    assert health_status["HealthyComponent.check_db"] is True
    
    assert "HealthyComponent.check_api" in health_status
    assert health_status["HealthyComponent.check_api"] is False
    
    assert "Health: check_db OK" in log_capture
    assert "Health: check_api FAILED" in log_capture

@pytest.mark.asyncio
async def test_aop_on_async_method():
    container = init(test_module)
    service = container.get(AsyncAuditedService)
    
    result = await service.do_async_work(10)
    
    assert result == 20
    assert "AUDIT_ASYNC - Entering: do_async_work" in log_capture
    assert "AsyncAuditedService: working..." in log_capture
    assert "AUDIT_ASYNC - Exiting: do_async_work" in log_capture

def test_proxy_serialization_pickle():
    container = init(test_module)
    
    lazy_proxy = container.get(MyLazyComponentForPickle)
    
    intercepted_proxy = container.get(AsyncAuditedService)
    
    try:
        pickled_lazy = pickle.dumps(lazy_proxy)
        pickled_intercepted = pickle.dumps(intercepted_proxy)
        
        unpickled_lazy = pickle.loads(pickled_lazy)
        unpickled_intercepted = pickle.loads(pickled_intercepted)
        
        assert unpickled_lazy.value == 42
        assert isinstance(unpickled_intercepted, AsyncAuditedService)
        
    except (pickle.PicklingError, SerializationError) as e:
        pytest.fail(f"Proxy serialization failed: {e}")

@pytest.mark.asyncio
async def test_event_bus_integration_and_shutdown():
    container = init([test_module, pico_ioc.event_bus])
    
    bus = container.get(EventBus)
    subscriber = container.get(MyTestSubscriber)
    
    assert isinstance(bus, EventBus)
    assert len(subscriber.received) == 0
    assert "Event received: Hello" not in log_capture
    
    await bus.publish(MyTestEvent("Hello"))
    
    assert subscriber.received == ["Hello"]
    assert "Event received: Hello" in log_capture
    
    await container.cleanup_all_async()
    
    with pytest.raises(EventBusClosedError):
        await bus.publish(MyTestEvent("Goodbye"))
        
