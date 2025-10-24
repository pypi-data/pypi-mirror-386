import pytest
import os
import json
import contextvars
from dataclasses import dataclass
from typing import List, Optional, Annotated, Callable, Any, Protocol
import logging
import time

from pico_ioc import (
    component, factory, provides, configuration, lazy, primary,
    conditional, scope, Qualifier, qualifier, intercepted_by, cleanup,
    init, PicoContainer, MethodInterceptor, MethodCtx,
    EnvSource, FileSource, ScopeProtocol, ContextVarScope, on_missing
)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log_capture = []

class ListLogHandler(logging.Handler):
    def emit(self, record):
        log_capture.append(self.format(record))

LOGGER = logging.getLogger("pico_ioc")
test_logger = logging.getLogger("TestLogger")
test_logger.addHandler(ListLogHandler())
test_logger.setLevel(logging.INFO)

@pytest.fixture(autouse=True)
def reset_logging_capture():
    log_capture.clear()

@pytest.fixture
def temp_config_file(tmp_path):
    file_path = tmp_path / "config.json"
    def _create(data: dict):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return str(file_path)
    return _create

class ServiceA: pass
class ServiceB: pass
class Database:
    def query(self, sql: str) -> str: return f"Query: {sql}"
class Cache:
    def get(self, key: str) -> Optional[str]: return None
    def set(self, key: str, value: str): pass

@component
class ServiceAImpl(ServiceA): pass

@component
class ServiceBImpl(ServiceB):
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

@component
@primary
class PostgresDB(Database):
    def query(self, sql: str) -> str:
        test_logger.info("Executing Postgres query")
        return f"Postgres: {sql}"

@component
class MysqlDB(Database):
     def query(self, sql: str) -> str:
        test_logger.info("Executing MySQL query")
        return f"MySQL: {sql}"

@component
@lazy
class LazyComponent:
    def __init__(self):
        test_logger.info("LazyComponent Instantiated!")
        self.created_at = time.time()

@configuration(prefix="APP_")
@dataclass
class AppConfig:
    DEBUG: bool = False
    TIMEOUT: int = 30
    DB_HOST: str = "localhost"

REQUEST_ID_VAR = contextvars.ContextVar("test_request_id", default=None)
request_scope = ContextVarScope(REQUEST_ID_VAR)

@component
@scope("request")
class RequestScopedData:
    def __init__(self):
        self.request_id = REQUEST_ID_VAR.get()
        test_logger.info(f"RequestScopedData created for request: {self.request_id}")

@component
class NeedsScoped:
    def __init__(self, req_data: RequestScopedData):
        self.req_data = req_data

PAYMENT = Qualifier("payment")
NOTIFICATION = Qualifier("notification")

class Sender(Protocol):
    def send(self, msg: str): ...

@component
@qualifier(PAYMENT)
class StripeSender(Sender):
    def send(self, msg: str): test_logger.info(f"Stripe: {msg}")

@component
@qualifier(PAYMENT)
class PaypalSender(Sender):
    def send(self, msg: str): test_logger.info(f"Paypal: {msg}")

@component
@qualifier(NOTIFICATION)
class EmailSender(Sender):
    def send(self, msg: str): test_logger.info(f"Email: {msg}")

@component
class PaymentService:
    def __init__(self, payment_senders: Annotated[List[Sender], PAYMENT]):
        self.senders = payment_senders

@component
class AuditInterceptor(MethodInterceptor):
    def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        test_logger.info(f"AUDIT - Entering: {ctx.cls.__name__}.{ctx.name}")
        result = call_next(ctx)
        test_logger.info(f"AUDIT - Exiting: {ctx.cls.__name__}.{ctx.name}")
        return result

audit = intercepted_by(AuditInterceptor)

@component
class AuditedService:
    @audit
    def perform_action(self, action_id: int):
        test_logger.info(f"Performing action {action_id}")
        return f"Action {action_id} done"

@component
@conditional(profiles=("prod",))
class RedisCache(Cache):
    def get(self, key: str) -> Optional[str]: return f"Redis:{key}"
    def set(self, key: str, value: str): test_logger.info("Redis SET")

@component
@on_missing(Cache)
class InMemoryCache(Cache):
     def get(self, key: str) -> Optional[str]: return f"Memory:{key}"
     def set(self, key: str, value: str): test_logger.info("Memory SET")

@component
class CacheClient:
    def __init__(self, cache: Cache):
        self.cache = cache

@component
class ResourceHolder:
    def __init__(self):
        self.closed = False
        test_logger.info("ResourceHolder created")

    @cleanup
    def close(self):
        self.closed = True
        test_logger.info("ResourceHolder closed")

test_module = type(os)('test_integration_module')
definitions = [
    ServiceA, ServiceB, Database, Cache, Sender,
    ServiceAImpl, ServiceBImpl, PostgresDB, MysqlDB, LazyComponent,
    AppConfig,
    RequestScopedData, NeedsScoped,
    StripeSender, PaypalSender, EmailSender, PaymentService,
    AuditInterceptor, AuditedService,
    RedisCache, InMemoryCache, CacheClient,
    ResourceHolder
]
for item in definitions:
    if hasattr(item, '__name__'):
        setattr(test_module, item.__name__, item)

test_scopes = {"request": request_scope}

def test_basic_di():
    container = init(test_module)
    instance_b = container.get(ServiceBImpl)
    assert isinstance(instance_b, ServiceBImpl)
    assert isinstance(instance_b.service_a, ServiceAImpl)
    instance_b_2 = container.get(ServiceBImpl)
    assert instance_b is instance_b_2

def test_configuration_injection_defaults():
    container = init(test_module, config=())
    config = container.get(AppConfig)
    assert isinstance(config, AppConfig)
    assert config.DEBUG is False
    assert config.TIMEOUT == 30
    assert config.DB_HOST == "localhost"

def test_configuration_injection_env(monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_TIMEOUT", "60")
    container = init(test_module, config=(EnvSource(prefix="APP_"),))
    config = container.get(AppConfig)
    assert config.DEBUG is True
    assert config.TIMEOUT == 60
    assert config.DB_HOST == "localhost"

def test_configuration_injection_file(temp_config_file):
    config_path = temp_config_file({"APP_DB_HOST": "remote.db", "APP_TIMEOUT": 90})
    container = init(test_module, config=(FileSource(config_path, prefix="APP_"),))
    config = container.get(AppConfig)
    assert config.DB_HOST == "remote.db"
    assert config.TIMEOUT == 90
    assert config.DEBUG is False

def test_configuration_precedence_env_over_file(monkeypatch, temp_config_file):
    monkeypatch.setenv("APP_TIMEOUT", "120")
    config_path = temp_config_file({"APP_TIMEOUT": 90})
    container = init(test_module, config=(EnvSource(prefix="APP_"), FileSource(config_path, prefix="APP_")))
    config = container.get(AppConfig)
    assert config.TIMEOUT == 120

def test_lazy_component_instantiation():
    container = init(test_module)
    assert "LazyComponent Instantiated!" not in log_capture
    proxy = container.get(LazyComponent)
    first_access_time = proxy.created_at
    assert "LazyComponent Instantiated!" in log_capture
    log_capture.clear()
    second_access_time = proxy.created_at
    assert first_access_time == second_access_time
    assert "LazyComponent Instantiated!" not in log_capture

def test_primary_component_wins():
    container = init(test_module)
    db = container.get(Database)
    assert isinstance(db, PostgresDB)

def test_conditional_component_active_by_profile():
    container_prod = init(test_module, profiles=("prod",))
    cache_client_prod = container_prod.get(CacheClient)
    assert isinstance(cache_client_prod.cache, RedisCache)

def test_on_missing_component_fallback():
    container_dev = init(test_module, profiles=("dev",))
    cache_client_dev = container_dev.get(CacheClient)
    assert isinstance(cache_client_dev.cache, InMemoryCache)

def test_request_scope():
    container = init(test_module, custom_scopes=test_scopes)
    token1 = container.activate_scope("request", "req-1")
    try:
        instance1_req1 = container.get(NeedsScoped)
        instance2_req1 = container.get(NeedsScoped)
        assert instance1_req1 is instance2_req1
        assert instance1_req1.req_data.request_id == "req-1"
        assert f"RequestScopedData created for request: req-1" in log_capture
        assert log_capture.count(f"RequestScopedData created for request: req-1") == 1
    finally:
        container.deactivate_scope("request", token1)
    log_capture.clear()
    token2 = container.activate_scope("request", "req-2")
    try:
        instance1_req2 = container.get(NeedsScoped)
        assert instance1_req2 is not instance1_req1
        assert instance1_req2.req_data.request_id == "req-2"
        assert f"RequestScopedData created for request: req-2" in log_capture
        assert log_capture.count(f"RequestScopedData created for request: req-2") == 1
    finally:
        container.deactivate_scope("request", token2)

def test_qualifier_injection():
    container = init(test_module)
    payment_service = container.get(PaymentService)
    assert len(payment_service.senders) == 2
    sender_types = {type(s) for s in payment_service.senders}
    assert sender_types == {StripeSender, PaypalSender}
    log_capture.clear()
    for sender in payment_service.senders:
        sender.send("Test message")
    assert any("Stripe: Test message" in msg for msg in log_capture)
    assert any("Paypal: Test message" in msg for msg in log_capture)
    assert all("Email:" not in msg for msg in log_capture)

def test_aop_interceptor_applied():
    container = init(test_module)
    audited_service = container.get(AuditedService)
    log_capture.clear()
    result = audited_service.perform_action(123)
    assert result == "Action 123 done"
    assert "AUDIT - Entering: AuditedService.perform_action" in log_capture
    assert "Performing action 123" in log_capture
    assert "AUDIT - Exiting: AuditedService.perform_action" in log_capture

def test_cleanup_called():
    container = init(test_module)
    holder = container.get(ResourceHolder)
    assert not holder.closed
    assert "ResourceHolder created" in log_capture
    log_capture.clear()
    container.cleanup_all()
    assert holder.closed
    assert "ResourceHolder closed" in log_capture
    
    
