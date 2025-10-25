class ApgardError(Exception):
    """Base exception for all Apgard SDK errors."""
    pass


class APIError(ApgardError):
    """API communication error."""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class ValidationError(ApgardError):
    """Invalid input."""
    pass
