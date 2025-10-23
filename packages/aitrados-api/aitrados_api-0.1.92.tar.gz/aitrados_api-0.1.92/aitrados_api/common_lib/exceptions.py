# exceptions.py


class DatasetError(Exception):
    """Base exception for Dataset API errors"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class RateLimitError(DatasetError):
    """Raised when API rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.retry_after is not None:
            return f"{base_msg} (retry after {self.retry_after:.1f} seconds)"
        return base_msg


class AuthenticationError(DatasetError):
    """Raised when API key is invalid or missing"""

    pass


class ValidationError(DatasetError):
    """Raised when request parameters are invalid"""

    pass


class ConfigError(DatasetError):
    """Raised when there's a configuration error"""

    pass
