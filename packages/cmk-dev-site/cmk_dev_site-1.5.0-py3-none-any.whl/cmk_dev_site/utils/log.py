import functools
import inspect
import logging
import sys
from collections.abc import Callable
from typing import Any, ClassVar, ParamSpec, TextIO, TypeVar, cast

PROGRESS_LEVEL = 25  # Between  INFO (20) and WARNING (30)


def colorize(text: str, color: str) -> str:
    """Colorize text with ANSI escape codes."""
    colors = {
        "blue": "\033[34m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "magenta": "\033[35;1m",
        "cyan": "\033[36m",
    }
    rest = "\033[0m"
    if color_code := colors.get(color):
        return f"{color_code}{text}{rest}"

    return text


P = ParamSpec("P")
T = TypeVar("T")


def generate_log_decorator(
    logger: logging.Logger,
):
    def log(
        info_message: str | None = None,
        error_message: str | None = None,
        message_info: Callable[P, str] | None = None,
        prefix: Callable[P, str] | None = None,
        max_level: int = logging.INFO,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator for logging function calls, handling errors with optional warnings

        :param info_message: The message to log before the function call.
        :param error_message: The message to log if the function raises an exception.
        :param message_info: A function to generate a custom info message based on the function's
            arguments.
        :param prefix: A function to generate a custom prefix for the info message based on the
            function's arguments.
        :param max_level: maximum logging level to use for logging message.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                formatted_func_name = func.__name__.replace("_", " ").capitalize()
                msg = (
                    message_info(*args, **kwargs)
                    if message_info
                    else info_message or f"{formatted_func_name}..."
                )

                msg = f"{prefix(*args, **kwargs) if prefix else ''}{msg}"

                # Log function call details
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Calling %s with args: %s, kwargs: %s",
                        colorize(func.__name__, "cyan"),
                        args,
                        kwargs,
                    )
                elif max_level >= logging.INFO:
                    logger.log(PROGRESS_LEVEL, msg)

                try:
                    result = func(*args, **kwargs)

                except Exception:  # pylint: disable=broad-except
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("%s Trace:", func.__name__, exc_info=True)
                    else:
                        logger.info("%s%s", msg, colorize("Failed", "red"))
                    if error_message:
                        logger.error(error_message)

                    # re-raise the exception
                    raise
                else:
                    # Log function result details
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("%s returned: %s", colorize(func.__name__, "cyan"), result)
                    elif max_level >= logging.INFO:
                        logger.info("%s", f"{msg}{colorize('OK', 'green')}")

                    return result

            return wrapper

        return decorator

    return log


class InlineStreamHandler(logging.StreamHandler[TextIO]):
    """Custom StreamHandler to support inline logging for progress updates."""

    def __init__(self):
        super().__init__(sys.stderr)
        self.current_inline_message = False

    def emit(self, record: logging.LogRecord) -> None:
        # Format the message
        msg = self.format(record)
        if record.levelno == PROGRESS_LEVEL:
            # Overwrite the same line for progress
            print(f"\r\033[K{msg}", end="", flush=True, file=sys.stderr)
            self.current_inline_message = True
        else:
            # Clear inline message if switching to a regular log
            if self.current_inline_message:
                print(f"\r\033[K{msg}", flush=True, file=sys.stderr)
                self.current_inline_message = False
            else:
                print(msg, flush=True, file=sys.stderr)


class ColoredFormatter(logging.Formatter):
    """Custom log formatter that colorizes log messages based on their level."""

    # Define ANSI escape codes for colors
    COLORS: ClassVar = {
        logging.DEBUG: "blue",  # Blue
        logging.INFO: "green",  # Green
        logging.WARNING: "yellow",  # Yellow
        logging.ERROR: "red",  # Red
        logging.CRITICAL: "magenta",  # Bright Magenta
        PROGRESS_LEVEL: "cyan",  # Cyan
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")

        # Colorize the levelname using termcolor
        record.levelname = colorize(record.levelname, color)

        # Call the parent format method to handle the message formatting
        return super().format(record)


class CustomLogger(logging.Logger):
    def progress(self, msg: str, *args: Any, **kwargs: Any):
        if self.isEnabledFor(PROGRESS_LEVEL):
            self.log(PROGRESS_LEVEL, msg, *args, **kwargs)


def get_logger(name: str) -> CustomLogger:
    logging.addLevelName(PROGRESS_LEVEL, "INFO")

    logging.setLoggerClass(CustomLogger)
    logger: CustomLogger = cast(CustomLogger, logging.getLogger(name))

    # Use the ColoredFormatter
    formatter = ColoredFormatter("%(levelname)s: %(message)s")
    console_handler = InlineStreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def add_method_logging(
    log: Callable[[Callable[P, T]], Callable[P, T]],
    methods: list[str] | None = None,
    prefix: str = "",
    exclude_methods: list[str] | None = None,
):
    """
    Class decorator that adds logging to specified methods or all public methods

    Args:
        methods: List of method names to log. If None, logs all public methods
        prefix: Prefix for log messages
        exclude_methods: Methods to exclude from logging
    """

    def class_decorator(cls: type[T]) -> type[T]:
        exclude_methods_set = set(exclude_methods or [])
        exclude_methods_set.update(["__init__", "__new__", "__del__"])

        if methods is None:
            # Get all public methods
            target_methods: list[Any] = [
                name
                for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
                if not name.startswith("_") and name not in exclude_methods_set
            ]
        else:
            target_methods = [m for m in methods if m not in exclude_methods_set]

        for method_name in target_methods:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                decorated_method = log(original_method)
                setattr(cls, method_name, decorated_method)

        return cls

    return class_decorator
