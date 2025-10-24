
## ADR-006: Eager Startup Validation

**Status:** Accepted

### Context

Dependency Injection containers can fail at runtime if a required dependency is missing or if there's an unresolvable circular dependency. These runtime failures, especially in production, can be hard to debug and lead to poor user experience. We prioritized application stability and predictability.

### Decision

We implemented **eager validation** during the `init()` process:

1.  **Dependency Graph Analysis:** After discovering all components and selecting the primary providers (`Registrar.select_and_bind`), the `Registrar._validate_bindings` method performs a static analysis of the dependency graph.
2.  **Check Dependencies:** For every registered component (excluding `@lazy` ones by default, though this could be configurable), it inspects the type hints of its `__init__` or factory `@provides` method.
3.  **Verify Providers:** For each required dependency type or key, it checks if a corresponding provider exists in the finalized `ComponentFactory`. It also handles list injections (`Annotated[List[Type], Qualifier]`) by checking if *any* provider matches the criteria.
4.  **Fail Fast:** If any required dependency cannot be satisfied, `init()` raises an `InvalidBindingError` immediately, listing all unsatisfied dependencies. Circular dependencies are typically caught during the recursive resolution simulation within validation or upon first actual resolution.

### Consequences

**Positive:** 👍
* **Significantly reduces runtime errors:** Most wiring issues (missing components, typos in keys) are caught at application startup.
* **Improves Developer Confidence:** If `init()` succeeds, the core dependency graph is guaranteed to be resolvable (barring runtime errors *within* component constructors).
* **Clear Error Reporting:** `InvalidBindingError` lists all problems found during validation.

**Negative:** 👎
* **Increased Startup Time:** The validation step adds overhead to the `init()` call, as it needs to inspect signatures and query the provider map. This is usually negligible for small-to-medium apps but could be noticeable for very large ones.
* **`@lazy` Components Bypass Validation:** Dependencies *only* required by `@lazy` components might not be validated at startup, potentially deferring a `ProviderNotFoundError` until the lazy component is first accessed (this is a deliberate trade-off for using `@lazy`).

