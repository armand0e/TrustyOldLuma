"""
Error management system for the Gaming Setup Tool.

This module provides comprehensive error handling, categorization,
retry mechanisms with exponential backoff, and user-friendly error messages.
"""

import asyncio
import logging
import platform
import sys
import time
from enum import Enum
from typing import Optional, Callable, TypeVar, Any, Dict, List, Tuple, Union, Type
from functools import wraps

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm

from exceptions import (
    GamingSetupError, 
    AdminPrivilegeError, 
    FileOperationError, 
    NetworkError, 
    ConfigurationError,
    SecurityConfigError
)
from config import PANEL_STYLES


# Type variable for generic function return type
T = TypeVar('T')


class ErrorCategory(Enum):
    """Categorization of errors by severity and handling approach."""
    
    # Critical errors that should stop execution
    CRITICAL = "critical"
    
    # Errors that can be recovered from
    RECOVERABLE = "recoverable"
    
    # Network-related errors that can be retried
    NETWORK = "network"
    
    # Platform-specific errors that may require graceful degradation
    PLATFORM = "platform"


class ErrorManager:
    """Manages error handling, categorization, and recovery strategies."""
    
    def __init__(self, console: Console):
        """Initialize the error manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
        self._error_registry: Dict[Type[Exception], ErrorCategory] = self._build_error_registry()
        self._solution_registry: Dict[Type[Exception], str] = self._build_solution_registry()
        self._platform_features: Dict[str, bool] = self._detect_platform_features()
    
    def _build_error_registry(self) -> Dict[Type[Exception], ErrorCategory]:
        """Build registry mapping exception types to error categories.
        
        Returns:
            Dictionary mapping exception types to error categories
        """
        return {
            # Critical errors
            AdminPrivilegeError: ErrorCategory.CRITICAL,
            PermissionError: ErrorCategory.CRITICAL,
            
            # Recoverable errors
            FileOperationError: ErrorCategory.RECOVERABLE,
            ConfigurationError: ErrorCategory.RECOVERABLE,
            SecurityConfigError: ErrorCategory.RECOVERABLE,
            FileNotFoundError: ErrorCategory.RECOVERABLE,
            
            # Network errors
            NetworkError: ErrorCategory.NETWORK,
            ConnectionError: ErrorCategory.NETWORK,
            TimeoutError: ErrorCategory.NETWORK,
            
            # Platform errors
            NotImplementedError: ErrorCategory.PLATFORM,
            OSError: ErrorCategory.PLATFORM
        }
    
    def _build_solution_registry(self) -> Dict[Type[Exception], str]:
        """Build registry mapping exception types to suggested solutions.
        
        Returns:
            Dictionary mapping exception types to solution strings
        """
        return {
            # Admin privilege errors
            AdminPrivilegeError: "Try running the application as administrator or with elevated privileges",
            PermissionError: "Check file permissions or run the application as administrator",
            
            # File operation errors
            FileOperationError: "Verify that files are not in use by another application",
            FileNotFoundError: "Check that required files exist in the expected locations",
            
            # Network errors
            NetworkError: "Check your internet connection and try again",
            ConnectionError: "Verify your internet connection or try again later",
            TimeoutError: "The operation timed out. Check your connection speed or try again later",
            
            # Configuration errors
            ConfigurationError: "Check configuration files for errors or reset to defaults",
            SecurityConfigError: "Try manually adding security exclusions as described in the documentation",
            
            # Platform errors
            NotImplementedError: "This feature is not supported on your operating system",
            OSError: "This operation may not be supported on your operating system"
        }
    
    def _detect_platform_features(self) -> Dict[str, bool]:
        """Detect available platform features for graceful degradation.
        
        Returns:
            Dictionary of platform features and their availability
        """
        system = platform.system().lower()
        
        return {
            "windows_admin": system == "windows",
            "windows_defender": system == "windows",
            "windows_shortcuts": system == "windows",
            "powershell": system == "windows",
            "linux_desktop_entries": system == "linux",
            "macos_aliases": system == "darwin"
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type.
        
        Args:
            error: Exception to categorize
            
        Returns:
            ErrorCategory for the given exception
        """
        # Check for exact type match
        if type(error) in self._error_registry:
            return self._error_registry[type(error)]
        
        # Check for parent class match
        for error_type, category in self._error_registry.items():
            if isinstance(error, error_type):
                return category
        
        # Default to recoverable for unknown errors
        return ErrorCategory.RECOVERABLE
    
    def get_solution(self, error: Exception) -> Optional[str]:
        """Get suggested solution for an error.
        
        Args:
            error: Exception to get solution for
            
        Returns:
            Suggested solution string, or None if no solution available
        """
        # Check for exact type match
        if type(error) in self._solution_registry:
            return self._solution_registry[type(error)]
        
        # Check for parent class match
        for error_type, solution in self._solution_registry.items():
            if isinstance(error, error_type):
                return solution
        
        return None
    
    def display_error(self, error: Exception, context: str) -> None:
        """Display error with category-appropriate styling and suggested solution.
        
        Args:
            error: Exception that occurred
            context: Context where the error occurred
        """
        category = self.categorize_error(error)
        solution = self.get_solution(error)
        
        error_text = Text()
        error_text.append(f"Context: {context}\n", style="bold")
        error_text.append(f"Error: {str(error)}\n", style="red")
        error_text.append(f"Category: {category.value.capitalize()}\n", style="yellow")
        
        if solution:
            error_text.append(f"\nSuggested Solution: {solution}", style="cyan")
            
        panel = Panel(
            error_text,
            title=f"❌ {category.value.capitalize()} Error",
            **PANEL_STYLES['error']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
        # Log the error with appropriate level based on category
        if category == ErrorCategory.CRITICAL:
            self.logger.critical(f"{context}: {str(error)}")
        elif category == ErrorCategory.NETWORK:
            self.logger.warning(f"Network error in {context}: {str(error)}")
        else:
            self.logger.error(f"{context}: {str(error)}")
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a platform-specific feature is available.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is available, False otherwise
        """
        return self._platform_features.get(feature_name, False)
    
    def handle_platform_limitation(self, feature_name: str, context: str) -> None:
        """Handle platform limitation with graceful degradation.
        
        Args:
            feature_name: Name of the unavailable feature
            context: Context where the feature was requested
        """
        warning_text = Text()
        warning_text.append(f"The feature '{feature_name}' is not available on your platform.\n", style="yellow")
        warning_text.append(f"Context: {context}\n", style="dim")
        warning_text.append("\nThe application will continue with reduced functionality.", style="cyan")
        
        panel = Panel(
            warning_text,
            title="⚠️ Platform Limitation",
            **PANEL_STYLES['warning']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
        self.logger.warning(f"Platform limitation: {feature_name} not available in {context}")


class RetryManager:
    """Manages retry logic with exponential backoff for operations."""
    
    def __init__(self, console: Console, max_attempts: int = 3, base_delay: float = 1.0):
        """Initialize the retry manager.
        
        Args:
            console: Rich console instance for output
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.console = console
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)
    
    async def retry_async(
        self, 
        func: Callable[..., Any], 
        *args: Any, 
        operation_name: str = "Operation", 
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs: Any
    ) -> Any:
        """Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Arguments to pass to the function
            operation_name: Name of the operation for logging
            retry_exceptions: Tuple of exception types to retry on
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        attempt = 1
        last_exception = None
        
        while attempt <= self.max_attempts:
            try:
                if attempt > 1:
                    self.logger.info(f"Retry attempt {attempt}/{self.max_attempts} for {operation_name}")
                    
                return await func(*args, **kwargs)
                
            except retry_exceptions as e:
                last_exception = e
                self.logger.warning(f"{operation_name} failed (attempt {attempt}/{self.max_attempts}): {str(e)}")
                
                if attempt < self.max_attempts:
                    # Calculate delay with exponential backoff
                    delay = self.base_delay * (2 ** (attempt - 1))
                    
                    # Add some randomness to prevent thundering herd
                    jitter = delay * 0.1 * (asyncio.get_event_loop().time() % 1.0)
                    delay += jitter
                    
                    self.console.print(f"[yellow]Retrying in {delay:.1f} seconds...[/yellow]")
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    self.logger.error(f"All {self.max_attempts} attempts failed for {operation_name}")
                    raise
        
        # This should never be reached due to the raise in the loop
        raise last_exception if last_exception else RuntimeError(f"All attempts failed for {operation_name}")
    
    def retry_sync(
        self, 
        func: Callable[..., T], 
        *args: Any, 
        operation_name: str = "Operation", 
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs: Any
    ) -> T:
        """Retry a synchronous function with exponential backoff.
        
        Args:
            func: Synchronous function to retry
            *args: Arguments to pass to the function
            operation_name: Name of the operation for logging
            retry_exceptions: Tuple of exception types to retry on
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        attempt = 1
        last_exception = None
        
        while attempt <= self.max_attempts:
            try:
                if attempt > 1:
                    self.logger.info(f"Retry attempt {attempt}/{self.max_attempts} for {operation_name}")
                    
                return func(*args, **kwargs)
                
            except retry_exceptions as e:
                last_exception = e
                self.logger.warning(f"{operation_name} failed (attempt {attempt}/{self.max_attempts}): {str(e)}")
                
                if attempt < self.max_attempts:
                    # Calculate delay with exponential backoff
                    delay = self.base_delay * (2 ** (attempt - 1))
                    
                    # Add some randomness to prevent thundering herd
                    jitter = delay * 0.1 * (time.time() % 1.0)
                    delay += jitter
                    
                    self.console.print(f"[yellow]Retrying in {delay:.1f} seconds...[/yellow]")
                    time.sleep(delay)
                    attempt += 1
                else:
                    self.logger.error(f"All {self.max_attempts} attempts failed for {operation_name}")
                    raise
        
        # This should never be reached due to the raise in the loop
        raise last_exception if last_exception else RuntimeError(f"All attempts failed for {operation_name}")
    
    def display_retry_prompt(self, operation: str, attempt: int) -> bool:
        """Display retry prompt and get user decision.
        
        Args:
            operation: Name of the operation that failed
            attempt: Current attempt number
            
        Returns:
            True if user wants to retry, False otherwise
        """
        retry_text = f"Operation '{operation}' failed (attempt {attempt}/{self.max_attempts})"
        
        if attempt < self.max_attempts:
            return Confirm.ask(f"{retry_text}. Would you like to retry?", default=True)
        else:
            self.console.print(f"[red]{retry_text}. Maximum attempts reached.[/red]")
            return False


# Decorator for retry with exponential backoff
def with_retry(
    max_attempts: int = 3, 
    base_delay: float = 1.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    operation_name: Optional[str] = None
):
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        retry_exceptions: Tuple of exception types to retry on
        operation_name: Name of the operation for logging
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create console for output
            console = Console() if 'console' not in kwargs else kwargs['console']
            
            # Create retry manager
            retry_manager = RetryManager(console, max_attempts, base_delay)
            
            # Get operation name
            op_name = operation_name or func.__name__
            
            # Retry the function
            return await retry_manager.retry_async(
                func, 
                *args, 
                operation_name=op_name,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create console for output
            console = Console() if 'console' not in kwargs else kwargs['console']
            
            # Create retry manager
            retry_manager = RetryManager(console, max_attempts, base_delay)
            
            # Get operation name
            op_name = operation_name or func.__name__
            
            # Retry the function
            return retry_manager.retry_sync(
                func, 
                *args, 
                operation_name=op_name,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context manager for platform-specific operations
class PlatformFeatureContext:
    """Context manager for platform-specific operations with graceful degradation."""
    
    def __init__(
        self, 
        error_manager: ErrorManager, 
        feature_name: str, 
        context: str,
        fallback_func: Optional[Callable[..., Any]] = None
    ):
        """Initialize the platform feature context.
        
        Args:
            error_manager: Error manager instance
            feature_name: Name of the platform feature
            context: Context where the feature is used
            fallback_func: Optional fallback function to call if feature is unavailable
        """
        self.error_manager = error_manager
        self.feature_name = feature_name
        self.context = context
        self.fallback_func = fallback_func
        self.feature_available = self.error_manager.is_feature_available(feature_name)
    
    def __enter__(self):
        """Enter the platform feature context."""
        if not self.feature_available:
            self.error_manager.handle_platform_limitation(self.feature_name, self.context)
        return self.feature_available
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the platform feature context."""
        if exc_type is not None and issubclass(exc_type, NotImplementedError):
            # Handle NotImplementedError as a platform limitation
            self.error_manager.handle_platform_limitation(self.feature_name, self.context)
            
            # Call fallback if provided
            if self.fallback_func is not None:
                self.fallback_func()
                
            # Suppress the exception
            return True
        
        return False


# Function to create user-friendly error messages
def create_user_friendly_message(error: Exception, context: str) -> str:
    """Create a user-friendly error message with context.
    
    Args:
        error: Exception that occurred
        context: Context where the error occurred
        
    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Map common error types to user-friendly messages
    friendly_messages = {
        "AdminPrivilegeError": "Administrator privileges are required but not available",
        "FileOperationError": "A file operation failed",
        "NetworkError": "A network operation failed",
        "ConfigurationError": "A configuration error occurred",
        "SecurityConfigError": "A security configuration error occurred",
        "FileNotFoundError": "A required file was not found",
        "PermissionError": "Permission denied for an operation",
        "ConnectionError": "Failed to connect to a network resource",
        "TimeoutError": "A network operation timed out"
    }
    
    # Get friendly message or use error message
    base_message = friendly_messages.get(error_type, error_msg)
    
    # Add context
    return f"{base_message} while {context}"