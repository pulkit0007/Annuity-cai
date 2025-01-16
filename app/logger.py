import logging
from rich.logging import RichHandler


class MultiLogFilter(logging.Filter):
    def __init__(self, log_names):
        self.log_names = log_names

    def filter(self, record):
        return record.name in self.log_names


def get_logger(
    log_name: str, log_level: int = logging.DEBUG, log_names_to_log=None
) -> logging.Logger:
    """
    Get a logger with Rich output and optional filtering by log names.

    Args:
        log_name (str): Name of the logger.
        log_level (int): The logging level (default: logging.INFO).
        log_names_to_log (list): List of log names to allow (default: None).

    Returns:
        logging.Logger: Configured logger.
    """
    if log_names_to_log is None:
        log_names_to_log = [
            "example_show",
            "default",
            "app",
            "orchestrator",
            "dispatcher",
            "testing",
            "streaming_utils",
            "training",
            "caching",
            "response_stream",
            "bot_response_processor",
            "tools",
            "intent_classifier",
        ]

    # Create a logger
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)

    # Create and configure Rich handler
    rich_handler = RichHandler()
    rich_handler.setLevel(log_level)

    # Add log filter
    filter = MultiLogFilter(log_names_to_log)
    rich_handler.addFilter(filter)

    # Avoid adding multiple handlers
    if not logger.hasHandlers():
        logger.addHandler(rich_handler)

    return logger


if __name__ == "__main__":
    """
    Example usage of the logger utility.
    """
    # Create a logger
    logger = get_logger("app", logging.DEBUG)

    # Log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Example: This won't print anything because the log name is not in the filter
    logger_2 = get_logger("other_log")
    logger_2.info("This log name is not in the allowed list")
