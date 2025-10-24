from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import Response
from centra_sdk.utils.context import IntegrationContextApi


T = TypeVar('T', bound=Callable)



class HandlerRegistry(Generic[T]):
    """A more sophisticated handler registry with decorator support and logging."""

    def __init__(self, name: str = "default"):
        self.name = name
        self._handlers: Dict[str, T] = {}
        self._logger = IntegrationContextApi.log()

    def register(self, tag: str = "default") -> Callable[[T], T]:
        """Decorator to register a handler.

        Usage:
            registry = HandlerRegistry()

            @registry.register("my_handler")
            def my_handler():
                pass
        """

        def decorator(handler: T) -> T:
            self._set_handler(tag, handler)
            return handler

        return decorator

    async def call_handler(
        self, func_name: str, token: str, *args, tag: str = "default", **kwargs
    ) -> Any:
        """Decorator to call a handler."""

        handler = self._get_handler(tag)
        if not handler:
            raise HTTPException(
                status_code=404, detail=f"handler for tag: {tag} not defined"
            )

        if hasattr(handler, 'validate_token'):
            if not handler.validate_token(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},)

        handler_func = getattr(handler, func_name, None) if handler else None
        if not handler_func:
            raise HTTPException(
                status_code=404, detail=f"failed to handle {tag}#{func_name}"
            )

        try:
            ret = await handler_func(*args, **kwargs)
            if isinstance(ret, (JSONResponse, Response)):
                return ret
            if ret:
                return JSONResponse(content=jsonable_encoder(ret), status_code=200)
            return
        except HTTPException as e:
            raise e
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    def _set_handler(self, tag: str, handler: T) -> None:
        """Register a handler for the given tag."""
        if not tag:
            raise ValueError("Tag cannot be empty")
        if not callable(handler):
            raise TypeError("Handler must be callable")

        if tag in self._handlers:
            self._logger.warning(
                f"Overriding existing handler for tag '{tag}' in registry '{self.name}'"
            )

        self._handlers[tag] = handler()
        self._logger.debug(
            f"Registered handler '{handler.__name__}' for tag '{tag}' in registry '{self.name}'"
        )

    def _get_handler(self, tag: str) -> Optional[T]:
        """Retrieve a handler for the given tag."""
        handler = self._handlers.get(tag)
        if handler is None:
            self._logger.warning(
                f"No handler found for tag '{tag}' in registry '{self.name}'"
            )
        return handler

    def has_handler(self, tag: str) -> bool:
        """Check if a handler exists for the given tag."""
        return tag in self._handlers

    def remove_handler(self, tag: str) -> bool:
        """Remove a handler for the given tag."""
        if tag in self._handlers:
            del self._handlers[tag]
            self._logger.debug(f"Removed handler for tag '{tag}' from registry '{self.name}'")
            return True
        return False

    def clear_handlers(self) -> None:
        """Remove all registered handlers."""
        count = len(self._handlers)
        self._handlers.clear()
        self._logger.debug(f"Cleared {count} handlers from registry '{self.name}'")

    def get_all_tags(self) -> list[str]:
        """Get all registered tags."""
        return list(self._handlers.keys())

    def __len__(self) -> int:
        """Return the number of registered handlers."""
        return len(self._handlers)

    def __contains__(self, tag: str) -> bool:
        """Check if a tag is registered (supports 'in' operator)."""
        return tag in self._handlers

    def __repr__(self) -> str:
        return f"HandlerRegistry(name='{self.name}', handlers={len(self._handlers)})"
