from __future__ import annotations

from typing import Any
from typing import Literal
from typing import TypeVar

T = TypeVar("T", bound=Any)


class ExecutionError(Exception):
    def __init__(
        self,
        inner_exception: Exception | None = None,
        message: str | None = None,
    ):
        super().__init__(message)
        self._message = message
        self._inner_exception = inner_exception

    @property
    def inner_exception(self) -> Exception | None:
        return self._inner_exception

    @property
    def message(self) -> str | None:
        return self._message


class RetryError(ExecutionError):
    def __init__(
        self,
        inner_exception: Exception,
        attempts: int,
        delay: int,
        backoff: int,
    ):
        super().__init__(inner_exception)
        self._attempts = attempts
        self._delay = delay
        self._backoff = backoff

    @property
    def retry_attempts(self) -> int:
        return self._attempts

    @property
    def retry_delay(self) -> int:
        return self._delay


class ExecutionTimeoutError(ExecutionError):
    def __init__(
        self,
        type: Literal["Workflow", "Task"],
        name: str,
        id: str,
        timeout: int,
    ):
        super().__init__(
            message=f"{type} {name} ({id}) timed out ({timeout}s).",
        )
        self._type = type
        self._name = name
        self._id = id
        self._timeout = timeout

    @property
    def timeout(self) -> int:
        return self._timeout

    def __reduce__(self):
        return (self.__class__, (self._type, self._name, self._id, self._timeout))


class PauseRequested(ExecutionError):
    def __init__(self, name: str):
        super().__init__(
            message="Pause Requested.",
        )
        self._name = name

    @property
    def name(self) -> str:
        return self._name


class WorkflowCatalogError(ExecutionError):
    def __init__(self, message: str):
        super().__init__(message=message)


class TaskNotFoundError(ExecutionError):
    def __init__(self):
        super().__init__(
            message="Task not found.",
        )


class WorkflowNotFoundError(ExecutionError):
    def __init__(self, name: str, module_name: str | None = None):
        super().__init__(
            message=f"Workflow '{name}' not found {f'in module {module_name}.' if module_name else ''}",
        )


class WorkflowAlreadyExistError(ExecutionError):
    def __init__(self, name: str):
        super().__init__(message=f"Workflow '{name}' already exists.")


class ExecutionContextNotFoundError(ExecutionError):
    def __init__(self, execution_id: str | None):
        super().__init__(
            message=f"Execution context '{execution_id}' not found.",
        )


class WorkerNotFoundError(ExecutionError):
    def __init__(self, name: str):
        super().__init__(message=f"Worker '{name}' not found.")


class DatabaseConnectionError(Exception):
    """Database connection related errors"""

    def __init__(
        self,
        message: str,
        database_type: str,
        original_error: Exception | None = None,
    ):
        self.database_type = database_type
        self.original_error = original_error
        super().__init__(message)


class PostgreSQLConnectionError(DatabaseConnectionError):
    """PostgreSQL-specific connection errors"""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message, "postgresql", original_error)
