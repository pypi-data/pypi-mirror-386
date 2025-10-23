"""
Hook factory system for dependency injection.

This module provides seamless integration with dependency-injector containers,
allowing hooks to be managed as container providers with full DI support.

Usage Pattern 1 - Container Integration (Recommended):
    ```python
    from dependency_injector import containers, providers
    from django_bulk_hooks import configure_hook_container

    class LoanAccountContainer(containers.DeclarativeContainer):
        loan_account_repository = providers.Singleton(LoanAccountRepository)
        loan_account_service = providers.Singleton(LoanAccountService)
        loan_account_validator = providers.Singleton(LoanAccountValidator)

        # Define hook as a provider
        loan_account_hook = providers.Singleton(
            LoanAccountHook,
            daily_loan_summary_service=Provide["daily_loan_summary_service"],
            loan_account_service=loan_account_service,
            loan_account_validator=loan_account_validator,
        )

    # Configure the hook system to use your container
    container = LoanAccountContainer()
    configure_hook_container(container)
    ```

Usage Pattern 2 - Explicit Factory Registration:
    ```python
    from django_bulk_hooks import set_hook_factory

    def create_loan_hook():
        return container.loan_account_hook()

    set_hook_factory(LoanAccountHook, create_loan_hook)
    ```

Usage Pattern 3 - Custom Resolver:
    ```python
    from django_bulk_hooks import configure_hook_container

    def custom_resolver(container, hook_cls, provider_name):
        # Custom resolution logic for nested containers
        return container.sub_container.get_provider(provider_name)()

    configure_hook_container(container, provider_resolver=custom_resolver)
    ```
"""

import logging
import re
import threading
from typing import Any, Callable, Optional, Type

logger = logging.getLogger(__name__)


class HookFactory:
    """
    Creates hook handler instances with dependency injection.

    Resolution order:
    1. Specific factory for hook class
    2. Container resolver (if configured)
    3. Direct instantiation
    """

    def __init__(self):
        """Initialize an empty factory."""
        self._specific_factories: dict[Type, Callable[[], Any]] = {}
        self._container_resolver: Optional[Callable[[Type], Any]] = None
        self._lock = threading.RLock()

    def register_factory(self, hook_cls: Type, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for a specific hook class.

        The factory function should accept no arguments and return an instance
        of the hook class with all dependencies injected.

        Args:
            hook_cls: The hook class to register a factory for
            factory: A callable that returns an instance of hook_cls

        Example:
            >>> def create_loan_hook():
            ...     return container.loan_account_hook()
            >>>
            >>> factory.register_factory(LoanAccountHook, create_loan_hook)
        """
        with self._lock:
            self._specific_factories[hook_cls] = factory
            name = getattr(hook_cls, "__name__", str(hook_cls))
            logger.debug(f"Registered factory for {name}")

    def configure_container(
        self,
        container: Any,
        provider_name_resolver: Optional[Callable[[Type], str]] = None,
        provider_resolver: Optional[Callable[[Any, Type, str], Any]] = None,
        fallback_to_direct: bool = True,
    ) -> None:
        """
        Configure the factory to use a dependency-injector container.

        This is the recommended way to integrate with dependency-injector.
        It automatically resolves hooks from container providers.

        Args:
            container: The dependency-injector container instance
            provider_name_resolver: Optional function to map hook class to provider name.
                                  Default: converts "LoanAccountHook" -> "loan_account_hook"
            provider_resolver: Optional function to resolve provider from container.
                             Signature: (container, hook_cls, provider_name) -> instance
                             Useful for nested container structures or custom resolution logic.
            fallback_to_direct: If True, falls back to direct instantiation when
                              provider not found. If False, raises error.

        Example (Standard Container):
            >>> class AppContainer(containers.DeclarativeContainer):
            ...     loan_service = providers.Singleton(LoanService)
            ...     loan_account_hook = providers.Singleton(
            ...         LoanAccountHook,
            ...         loan_service=loan_service,
            ...     )
            >>>
            >>> container = AppContainer()
            >>> factory.configure_container(container)

        Example (Custom Resolver for Nested Containers):
            >>> def resolve_nested(container, hook_cls, provider_name):
            ...     # Navigate nested structure
            ...     sub_container = container.loan_accounts_container()
            ...     return getattr(sub_container, provider_name)()
            >>>
            >>> factory.configure_container(
            ...     container,
            ...     provider_resolver=resolve_nested
            ... )
        """
        name_resolver = provider_name_resolver or self._default_name_resolver

        def resolver(hook_cls: Type) -> Any:
            """Resolve hook instance from the container."""
            provider_name = name_resolver(hook_cls)
            name = getattr(hook_cls, "__name__", str(hook_cls))

            # If custom provider resolver is provided, use it
            if provider_resolver is not None:
                logger.debug(f"Resolving {name} using custom provider resolver")
                try:
                    return provider_resolver(container, hook_cls, provider_name)
                except Exception as e:
                    if fallback_to_direct:
                        logger.debug(
                            f"Custom provider resolver failed for {name} ({e}), "
                            f"falling back to direct instantiation"
                        )
                        return hook_cls()
                    raise

            # Default resolution: look for provider directly on container
            if hasattr(container, provider_name):
                provider = getattr(container, provider_name)
                logger.debug(
                    f"Resolving {name} from container provider '{provider_name}'"
                )
                # Call the provider to get the instance
                return provider()

            if fallback_to_direct:
                logger.debug(
                    f"Provider '{provider_name}' not found in container for {name}, "
                    f"falling back to direct instantiation"
                )
                return hook_cls()

            raise ValueError(
                f"Hook {name} not found in container. "
                f"Expected provider name: '{provider_name}'. "
                f"Available providers: {[p for p in dir(container) if not p.startswith('_')]}"
            )

        with self._lock:
            self._container_resolver = resolver
            container_name = getattr(
                container.__class__, "__name__", str(container.__class__)
            )
            logger.info(
                f"Configured hook factory to use container: {container_name}"
            )

    def create(self, hook_cls: Type) -> Any:
        """
        Create a hook instance using the configured resolution strategy.

        Resolution order:
        1. Specific factory registered via register_factory()
        2. Container resolver configured via configure_container()
        3. Direct instantiation hook_cls()

        Args:
            hook_cls: The hook class to instantiate

        Returns:
            An instance of the hook class

        Raises:
            Any exception raised by the factory, container, or constructor
        """
        with self._lock:
            # 1. Check for specific factory
            if hook_cls in self._specific_factories:
                factory = self._specific_factories[hook_cls]
                name = getattr(hook_cls, "__name__", str(hook_cls))
                logger.debug(f"Using specific factory for {name}")
                return factory()

            # 2. Check for container resolver
            if self._container_resolver is not None:
                name = getattr(hook_cls, "__name__", str(hook_cls))
                logger.debug(f"Using container resolver for {name}")
                return self._container_resolver(hook_cls)

            # 3. Fall back to direct instantiation
            name = getattr(hook_cls, "__name__", str(hook_cls))
            logger.debug(f"Using direct instantiation for {name}")
            return hook_cls()

    def clear(self) -> None:
        """
        Clear all registered factories and container configuration.
        Useful for testing.
        """
        with self._lock:
            self._specific_factories.clear()
            self._container_resolver = None
            logger.debug("Cleared all hook factories and container configuration")

    def is_container_configured(self) -> bool:
        """
        Check if a container resolver is configured.

        Returns:
            True if configure_container() has been called
        """
        with self._lock:
            return self._container_resolver is not None

    def has_factory(self, hook_cls: Type) -> bool:
        """
        Check if a hook class has a registered factory.

        Args:
            hook_cls: The hook class to check

        Returns:
            True if a specific factory is registered, False otherwise
        """
        with self._lock:
            return hook_cls in self._specific_factories

    def get_factory(self, hook_cls: Type) -> Optional[Callable[[], Any]]:
        """
        Get the registered factory for a specific hook class.

        Args:
            hook_cls: The hook class to look up

        Returns:
            The registered factory function, or None if not registered
        """
        with self._lock:
            return self._specific_factories.get(hook_cls)

    def list_factories(self) -> dict[Type, Callable]:
        """
        Get a copy of all registered hook factories.

        Returns:
            A dictionary mapping hook classes to their factory functions
        """
        with self._lock:
            return self._specific_factories.copy()

    @staticmethod
    def _default_name_resolver(hook_cls: Type) -> str:
        """
        Default naming convention: LoanAccountHook -> loan_account_hook

        Args:
            hook_cls: Hook class to convert

        Returns:
            Snake-case provider name
        """
        name = hook_cls.__name__
        # Convert CamelCase to snake_case
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return snake_case


# Global singleton factory
_factory: Optional[HookFactory] = None
_factory_lock = threading.Lock()


def get_factory() -> HookFactory:
    """
    Get the global hook factory instance.

    Creates the factory on first access (singleton pattern).
    Thread-safe initialization.

    Returns:
        HookFactory singleton instance
    """
    global _factory

    if _factory is None:
        with _factory_lock:
            # Double-checked locking
            if _factory is None:
                _factory = HookFactory()

    return _factory


# Backward-compatible module-level functions
def set_hook_factory(hook_cls: Type, factory: Callable[[], Any]) -> None:
    """
    Register a factory function for a specific hook class.

    The factory function should accept no arguments and return an instance
    of the hook class with all dependencies injected.

    Args:
        hook_cls: The hook class to register a factory for
        factory: A callable that returns an instance of hook_cls

    Example:
        >>> def create_loan_hook():
        ...     return container.loan_account_hook()
        >>>
        >>> set_hook_factory(LoanAccountHook, create_loan_hook)
    """
    hook_factory = get_factory()
    hook_factory.register_factory(hook_cls, factory)


def set_default_hook_factory(factory: Callable[[Type], Any]) -> None:
    """
    DEPRECATED: Use configure_hook_container with provider_resolver instead.

    This function is kept for backward compatibility but is no longer recommended.
    Use configure_hook_container with a custom provider_resolver for similar functionality.

    Args:
        factory: A callable that takes a class and returns an instance
    """
    import warnings

    warnings.warn(
        "set_default_hook_factory is deprecated. "
        "Use configure_hook_container with provider_resolver instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Convert to container-style resolver
    def container_resolver(hook_cls):
        return factory(hook_cls)

    hook_factory = get_factory()
    hook_factory._container_resolver = container_resolver


def configure_hook_container(
    container: Any,
    provider_name_resolver: Optional[Callable[[Type], str]] = None,
    provider_resolver: Optional[Callable[[Any, Type, str], Any]] = None,
    fallback_to_direct: bool = True,
) -> None:
    """
    Configure the hook system to use a dependency-injector container.

    This is the recommended way to integrate with dependency-injector.
    It automatically resolves hooks from container providers.

    Args:
        container: The dependency-injector container instance
        provider_name_resolver: Optional function to map hook class to provider name.
                              Default: converts "LoanAccountHook" -> "loan_account_hook"
        provider_resolver: Optional function to resolve provider from container.
                         Signature: (container, hook_cls, provider_name) -> instance
                         Useful for nested container structures.
        fallback_to_direct: If True, falls back to direct instantiation when
                          provider not found. If False, raises error.

    Example:
        >>> container = AppContainer()
        >>> configure_hook_container(container)
    """
    hook_factory = get_factory()
    hook_factory.configure_container(
        container,
        provider_name_resolver=provider_name_resolver,
        provider_resolver=provider_resolver,
        fallback_to_direct=fallback_to_direct,
    )


def configure_nested_container(
    container: Any,
    container_path: str,
    provider_name_resolver: Optional[Callable[[Type], str]] = None,
    fallback_to_direct: bool = True,
) -> None:
    """
    DEPRECATED: Use configure_hook_container with provider_resolver instead.

    Configure the hook system for nested/hierarchical container structures.
    This is now handled better by passing a custom provider_resolver to
    configure_hook_container.

    Args:
        container: The root dependency-injector container
        container_path: Dot-separated path to sub-container (e.g., "loan_accounts_container")
        provider_name_resolver: Optional function to map hook class to provider name
        fallback_to_direct: If True, falls back to direct instantiation when provider not found

    Example:
        >>> # Instead of this:
        >>> configure_nested_container(app_container, "loan_accounts_container")
        >>>
        >>> # Use this:
        >>> def resolve_nested(container, hook_cls, provider_name):
        ...     sub = container.loan_accounts_container()
        ...     return getattr(sub, provider_name)()
        >>> configure_hook_container(app_container, provider_resolver=resolve_nested)
    """
    import warnings

    warnings.warn(
        "configure_nested_container is deprecated. "
        "Use configure_hook_container with provider_resolver instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    def nested_resolver(container_obj, hook_cls, provider_name):
        """Navigate to sub-container and get provider."""
        # Navigate to sub-container
        current = container_obj
        for part in container_path.split("."):
            if not hasattr(current, part):
                raise ValueError(
                    f"Container path '{container_path}' not found. Missing: {part}"
                )
            provider = getattr(current, part)
            # Call provider to get next level
            current = provider()

        # Get the hook provider from sub-container
        if not hasattr(current, provider_name):
            raise ValueError(
                f"Provider '{provider_name}' not found in sub-container. "
                f"Available: {[p for p in dir(current) if not p.startswith('_')]}"
            )

        hook_provider = getattr(current, provider_name)
        logger.debug(
            f"Resolved {hook_cls.__name__} from {container_path}.{provider_name}"
        )
        return hook_provider()

    configure_hook_container(
        container,
        provider_name_resolver=provider_name_resolver,
        provider_resolver=nested_resolver,
        fallback_to_direct=fallback_to_direct,
    )


def clear_hook_factories() -> None:
    """
    Clear all registered hook factories and container configuration.
    Useful for testing.
    """
    hook_factory = get_factory()
    hook_factory.clear()


def create_hook_instance(hook_cls: Type) -> Any:
    """
    Create a hook instance using the configured resolution strategy.

    Resolution order:
    1. Specific factory registered via set_hook_factory()
    2. Container resolver configured via configure_hook_container()
    3. Direct instantiation hook_cls()

    Args:
        hook_cls: The hook class to instantiate

    Returns:
        An instance of the hook class

    Raises:
        Any exception raised by the factory, container, or constructor
    """
    hook_factory = get_factory()
    return hook_factory.create(hook_cls)


def get_hook_factory(hook_cls: Type) -> Optional[Callable[[], Any]]:
    """
    Get the registered factory for a specific hook class.

    Args:
        hook_cls: The hook class to look up

    Returns:
        The registered factory function, or None if not registered
    """
    hook_factory = get_factory()
    return hook_factory.get_factory(hook_cls)


def has_hook_factory(hook_cls: Type) -> bool:
    """
    Check if a hook class has a registered factory.

    Args:
        hook_cls: The hook class to check

    Returns:
        True if a specific factory is registered, False otherwise
    """
    hook_factory = get_factory()
    return hook_factory.has_factory(hook_cls)


def is_container_configured() -> bool:
    """
    Check if a container resolver is configured.

    Returns:
        True if configure_hook_container() has been called
    """
    hook_factory = get_factory()
    return hook_factory.is_container_configured()


def list_registered_factories() -> dict[Type, Callable]:
    """
    Get a copy of all registered hook factories.

    Returns:
        A dictionary mapping hook classes to their factory functions
    """
    hook_factory = get_factory()
    return hook_factory.list_factories()
