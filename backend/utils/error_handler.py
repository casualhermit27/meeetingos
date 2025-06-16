"""
Custom exception classes and error handling utilities
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAPIError(Exception):
    """Base exception class for API errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class AuthenticationError(BaseAPIError):
    """Authentication related errors"""
    pass


class AuthorizationError(BaseAPIError):
    """Authorization related errors"""
    pass


class ValidationError(BaseAPIError):
    """Data validation errors"""
    pass


class DatabaseError(BaseAPIError):
    """Database operation errors"""
    pass


class StorageError(BaseAPIError):
    """File storage operation errors"""
    pass


class ZoomAPIError(BaseAPIError):
    """Zoom API related errors"""
    pass


class FileMonitorError(BaseAPIError):
    """File monitoring service errors"""
    pass


class ProcessingError(BaseAPIError):
    """Recording processing errors"""
    pass


class ConfigurationError(BaseAPIError):
    """Configuration related errors"""
    pass


class RateLimitError(BaseAPIError):
    """Rate limiting errors"""
    pass


class AppErrorHandler:
    """Application error handler with logging and notification capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.notification_threshold = 5  # Send notification after 5 errors of same type
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error with logging and optional notifications
        
        Args:
            error: The exception to handle
            context: Additional context information
            
        Returns:
            Error response dictionary
        """
        context = context or {}
        
        # Generate error ID for tracking
        error_id = self._generate_error_id()
        
        # Prepare error info
        error_info = {
            "error_id": error_id,
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add details if it's a custom API error
        if isinstance(error, BaseAPIError):
            error_info.update(error.to_dict())
        
        # Log the error
        self._log_error(error, error_info, context)
        
        # Track error frequency
        self._track_error_frequency(type(error).__name__)
        
        # Check if we should send notifications
        self._check_notification_threshold(type(error).__name__)
        
        return error_info
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _log_error(self, error: Exception, error_info: Dict[str, Any], context: Dict[str, Any]):
        """Log error with appropriate level based on error type"""
        
        log_message = f"Error {error_info['error_id']}: {error_info['message']}"
        
        if context:
            log_message += f" | Context: {context}"
        
        # Log with stack trace for non-API errors
        if not isinstance(error, BaseAPIError):
            log_message += f"\nStacktrace:\n{traceback.format_exc()}"
        
        # Choose log level based on error type
        if isinstance(error, (ValidationError, AuthenticationError, AuthorizationError)):
            self.logger.warning(log_message)
        elif isinstance(error, (DatabaseError, StorageError, ZoomAPIError)):
            self.logger.error(log_message)
        elif isinstance(error, (ConfigurationError, FileMonitorError)):
            self.logger.critical(log_message)
        else:
            self.logger.error(log_message)
    
    def _track_error_frequency(self, error_type: str):
        """Track frequency of error types"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = {
                "count": 0,
                "last_occurrence": None,
                "first_occurrence": datetime.utcnow()
            }
        
        self.error_counts[error_type]["count"] += 1
        self.error_counts[error_type]["last_occurrence"] = datetime.utcnow()
    
    def _check_notification_threshold(self, error_type: str):
        """Check if error threshold is reached for notifications"""
        error_stats = self.error_counts.get(error_type, {})
        count = error_stats.get("count", 0)
        
        if count >= self.notification_threshold and count % self.notification_threshold == 0:
            self._send_error_notification(error_type, error_stats)
    
    def _send_error_notification(self, error_type: str, error_stats: Dict[str, Any]):
        """Send error notification (placeholder for actual notification system)"""
        self.logger.critical(
            f"ERROR THRESHOLD REACHED: {error_type} has occurred {error_stats['count']} times. "
            f"First occurrence: {error_stats['first_occurrence']}. "
            f"Last occurrence: {error_stats['last_occurrence']}"
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(stats["count"] for stats in self.error_counts.values()),
            "unique_error_types": len(self.error_counts)
        }
    
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_counts.clear()
        self.logger.info("Error statistics reset")


class RetryableError(BaseAPIError):
    """Base class for errors that can be retried"""
    
    def __init__(self, message: str, retry_after: int = 60, max_retries: int = 3, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after  # Seconds to wait before retry
        self.max_retries = max_retries


class CircuitBreakerError(BaseAPIError):
    """Error when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failure in circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


def handle_async_errors(func):
    """Decorator for handling async function errors"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseAPIError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            # Convert unknown errors to ProcessingError
            raise ProcessingError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                details={"function": func.__name__, "args": str(args)[:100]}
            )
    
    return wrapper


def handle_sync_errors(func):
    """Decorator for handling sync function errors"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseAPIError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            # Convert unknown errors to ProcessingError
            raise ProcessingError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                details={"function": func.__name__, "args": str(args)[:100]}
            )
    
    return wrapper


class ErrorContext:
    """Context manager for adding error context"""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.error_handler = AppErrorHandler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error_handler.handle_error(exc_val, self.context)
        return False  # Don't suppress the exception


# Utility functions for error handling
def safe_execute(func, default_value=None, error_types=None):
    """
    Safely execute a function and return default value on error
    
    Args:
        func: Function to execute
        default_value: Value to return on error
        error_types: Tuple of exception types to catch (default: all)
    
    Returns:
        Function result or default value
    """
    error_types = error_types or (Exception,)
    
    try:
        return func()
    except error_types as e:
        logging.warning(f"Safe execution failed for {func}: {str(e)}")
        return default_value


async def safe_execute_async(func, default_value=None, error_types=None):
    """
    Safely execute an async function and return default value on error
    
    Args:
        func: Async function to execute
        default_value: Value to return on error
        error_types: Tuple of exception types to catch (default: all)
    
    Returns:
        Function result or default value
    """
    error_types = error_types or (Exception,)
    
    try:
        return await func()
    except error_types as e:
        logging.warning(f"Safe async execution failed for {func}: {str(e)}")
        return default_value


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in data
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {missing_fields}",
            details={"missing_fields": missing_fields, "provided_fields": list(data.keys())}
        )


def validate_file_size(file_size: int, max_size: int) -> None:
    """
    Validate file size
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
    
    Raises:
        ValidationError: If file size exceeds maximum
    """
    if file_size > max_size:
        raise ValidationError(
            f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)",
            details={"file_size": file_size, "max_size": max_size}
        ) 