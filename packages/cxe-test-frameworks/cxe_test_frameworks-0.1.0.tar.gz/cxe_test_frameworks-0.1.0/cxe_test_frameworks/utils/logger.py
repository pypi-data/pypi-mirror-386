"""
Logger Configuration for Test Automation

Provides centralized logging configuration with structured logging support,
multiple output formats, and configurable log levels.

Extracted from production tests for reuse across CXE services.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import colorlog
import structlog


class NoFlushFileHandler(logging.FileHandler):
    """Custom FileHandler that doesn't flush to avoid container filesystem issues."""

    def flush(self):
        """Override flush to avoid OSError in container environments."""
        try:
            super().flush()
        except OSError as e:
            # Silently ignore flush errors in container environments
            if e.errno == 95:  # Operation not supported
                pass
            else:
                raise


class LoggerConfig:
    """
    Centralized logger configuration and management.

    Provides structured logging with colorized console output,
    file rotation, and configurable log levels for different components.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _configured = False

    @classmethod
    def configure_logging(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Configure global logging settings.

        Args:
            config (Dict[str, Any], optional): Logging configuration
        """
        if cls._configured:
            return

        config = config or cls._get_default_config()

        # Create logs directory
        log_dir = config.get("log_dir", "reports/logs")
        os.makedirs(log_dir, exist_ok=True)

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str, config: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        Get or create a logger with the specified name.

        Args:
            name (str): Logger name
            config (Dict[str, Any], optional): Logger-specific configuration

        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._configured:
            cls.configure_logging(config)

        if name in cls._loggers:
            return cls._loggers[name]

        config = config or cls._get_default_config()
        logger = cls._create_logger(name, config)
        cls._loggers[name] = logger

        return logger

    @classmethod
    def _create_logger(cls, name: str, config: Dict[str, Any]) -> logging.Logger:
        """
        Create a new logger with the specified configuration.

        Args:
            name (str): Logger name
            config (Dict[str, Any]): Logger configuration

        Returns:
            logging.Logger: Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.get("level", "INFO")))

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Console handler with colors
        if config.get("console_logging", True):
            console_handler = colorlog.StreamHandler()
            console_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        # Check environment variable to completely disable file logging if needed
        disable_file_logging = os.environ.get("DISABLE_FILE_LOGGING", "").lower() in (
            "true",
            "1",
            "yes",
        )

        if config.get("file_logging", True) and not disable_file_logging:
            try:
                log_dir = config.get("log_dir", "reports/logs")
                log_file = os.path.join(log_dir, f"{name}.log")

                # Use custom NoFlushFileHandler to avoid flush issues in containers
                file_handler = NoFlushFileHandler(log_file, mode="a")

                file_formatter = logging.Formatter(  # noqa: E501
                    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",  # noqa: E501
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except (OSError, IOError) as e:
                # If file logging fails completely, continue with console logging only
                print(f"Warning: File logging disabled due to error: {e}", file=sys.stderr)

        # Test execution log (separate file for test runs)
        if config.get("test_logging", True) and not disable_file_logging:
            try:
                log_dir = config.get("log_dir", "reports/logs")
                test_log_file = os.path.join(log_dir, "test_execution.log")

                # Use custom NoFlushFileHandler to avoid flush issues in containers
                test_handler = NoFlushFileHandler(test_log_file, mode="a")

                test_formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                test_handler.setFormatter(test_formatter)
                logger.addHandler(test_handler)
            except (OSError, IOError) as e:
                # If test logging fails completely, continue with console logging only
                print(f"Warning: Test file logging disabled due to error: {e}", file=sys.stderr)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

        return logger

    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """
        Get default logging configuration.

        Returns:
            Dict[str, Any]: Default logging configuration
        """
        return {
            "level": "INFO",
            "console_logging": True,
            "file_logging": True,
            "test_logging": True,
            "log_dir": "reports/logs",
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
        }

    @classmethod
    def set_log_level(cls, level: str) -> None:
        """
        Set log level for all configured loggers.

        Args:
            level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)

        for logger in cls._loggers.values():
            logger.setLevel(log_level)

    @classmethod
    def log_test_start(cls, test_name: str, logger_name: str = "test_executor") -> None:
        """
        Log test execution start.

        Args:
            test_name (str): Name of the test being started
            logger_name (str): Logger name to use
        """
        logger = cls.get_logger(logger_name)
        logger.info(f"Test started: {test_name}")

    @classmethod
    def log_test_end(
        cls, test_name: str, status: str, duration: float = 0.0, logger_name: str = "test_executor"
    ) -> None:
        """
        Log test execution end.

        Args:
            test_name (str): Name of the test that ended
            status (str): Test status (PASSED, FAILED, SKIPPED)
            duration (float): Test execution duration in seconds
            logger_name (str): Logger name to use
        """
        logger = cls.get_logger(logger_name)
        logger.info(f"Test ended: {test_name} - Status: {status} - Duration: {duration:.2f}s")

    @classmethod
    def log_error_with_context(
        cls, error: Exception, context: Dict[str, Any], logger_name: str = "error_handler"
    ) -> None:
        """
        Log error with additional context information.

        Args:
            error (Exception): Exception that occurred
            context (Dict[str, Any]): Additional context information
            logger_name (str): Logger name to use
        """
        # Use structlog for structured error logging
        struct_logger = structlog.get_logger(logger_name)
        struct_logger.error(
            "Exception occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            **context,
        )

    @classmethod
    def create_test_session_logger(cls, session_id: str) -> logging.Logger:
        """
        Create a logger for a specific test session.

        Args:
            session_id (str): Unique session identifier

        Returns:
            logging.Logger: Session-specific logger
        """
        logger_name = f"session_{session_id}"
        config = cls._get_default_config()

        # Create session-specific log file
        config["log_dir"] = "reports/logs/sessions"
        os.makedirs(config["log_dir"], exist_ok=True)

        return cls.get_logger(logger_name, config)

    @classmethod
    def cleanup_old_logs(cls, days_to_keep: int = 7) -> None:
        """
        Clean up log files older than specified days.

        Args:
            days_to_keep (int): Number of days to keep log files
        """
        try:
            log_dir = "reports/logs"
            if not os.path.exists(log_dir):
                return

            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            print(f"Removed old log file: {file_path}")

        except Exception as e:
            print(f"Error cleaning up logs: {e}")


# Convenience function for quick logger access
def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Configured logger
    """
    return LoggerConfig.get_logger(name)
