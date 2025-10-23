"""Custom exceptions for Nexus filesystem operations."""


class NexusError(Exception):
    """Base exception for all Nexus errors."""

    def __init__(self, message: str, path: str | None = None):
        self.message = message
        self.path = path
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with optional path."""
        if self.path:
            return f"{self.message}: {self.path}"
        return self.message


class NexusFileNotFoundError(NexusError, FileNotFoundError):
    """Raised when a file or directory does not exist."""

    def __init__(self, path: str, message: str | None = None):
        msg = message or "File not found"
        super().__init__(msg, path)


class NexusPermissionError(NexusError):
    """Raised when access to a file or directory is denied."""

    def __init__(self, path: str, message: str | None = None):
        msg = message or "Permission denied"
        super().__init__(msg, path)


class BackendError(NexusError):
    """Raised when a backend operation fails."""

    def __init__(self, message: str, backend: str | None = None, path: str | None = None):
        self.backend = backend
        if backend:
            message = f"[{backend}] {message}"
        super().__init__(message, path)


class InvalidPathError(NexusError):
    """Raised when a path is invalid or contains illegal characters."""

    def __init__(self, path: str, message: str | None = None):
        msg = message or "Invalid path"
        super().__init__(msg, path)


class MetadataError(NexusError):
    """Raised when metadata operations fail."""

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message, path)


class ValidationError(NexusError):
    """Raised when validation fails.

    This is a domain error that should be caught and converted to
    appropriate HTTP status codes (400 Bad Request) in API layers.

    Examples:
        >>> raise ValidationError("name is required")
        >>> raise ValidationError("size cannot be negative", path="/data/file.txt")
    """

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message, path)


class ParserError(NexusError):
    """Raised when document parsing fails."""

    def __init__(self, message: str, path: str | None = None, parser: str | None = None):
        self.parser = parser
        if parser:
            message = f"[{parser}] {message}"
        super().__init__(message, path)


class ConflictError(NexusError):
    """Raised when optimistic concurrency check fails.

    This occurs when a write operation specifies an if_match etag/version
    that doesn't match the current file version, indicating another agent
    has modified the file concurrently.

    Agents must handle this error explicitly by:
    1. Retrying with a fresh read
    2. Merging changes
    3. Aborting the operation
    4. Force overwriting (dangerous)

    Examples:
        >>> try:
        ...     nx.write(path, content, if_match=old_etag)
        ... except ConflictError as e:
        ...     print(f"Conflict: expected {e.expected_etag}, got {e.current_etag}")
        ...     # Retry with fresh read
        ...     result = nx.read(path, return_metadata=True)
        ...     nx.write(path, content, if_match=result['etag'])
    """

    def __init__(self, path: str, expected_etag: str, current_etag: str):
        """Initialize conflict error.

        Args:
            path: Virtual file path that had the conflict
            expected_etag: The etag value that was expected (from if_match)
            current_etag: The actual current etag value in the database
        """
        self.expected_etag = expected_etag
        self.current_etag = current_etag
        message = (
            f"Conflict detected - file was modified by another agent. "
            f"Expected etag '{expected_etag[:16]}...', but current etag is '{current_etag[:16]}...'"
        )
        super().__init__(message, path)


# Alias for convenience (used in time-travel debugging)
NotFoundError = NexusFileNotFoundError
