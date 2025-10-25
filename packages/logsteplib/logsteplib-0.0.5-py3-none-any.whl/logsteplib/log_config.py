"""
Standard logger configuration library.
"""

import logging
import sys


class LogConfig:
    """
    A configurable logger for console output using Python's logging module.

    This class sets up a stream logger with a standardised format and suppresses noisy loggers such as 'py4j'. It is
    intended for use in scripts and applications that require consistent and readable logging output.
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialise the logger with a given name and logging level.

        Args:
            name (str): The name of the logger.
            level (int, optional): The logging level (e.g., logging.INFO, logging.DEBUG).
              Defaults to logging.INFO.
        """
        self.name = name
        self.level = level
        # Custom formatter
        self.formatter = logging.Formatter(fmt=self.get_std_fmt(), datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = self._setup_logger()

    def get_std_fmt(self) -> str:
        """
        Return the standard format string for log messages.

        Returns:
            str: A format string including timestamp, logger name, level, and message.
        """
        return "%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s"

    def _setup_logger(self) -> logging.Logger:
        """
        Configure and return a logger instance with a stream handler.

        Clears existing handlers, disables propagation, and applies a custom formatter.
        Also suppresses the 'py4j' logger to reduce console noise.

        Returns:
            logging.Logger: A configured logger instance.
        """
        # Logger configuration
        logger = logging.getLogger(self.name)

        # Sets log level to INFO (default)
        logger.setLevel(self.level)

        # Clears existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Disable propagation to prevent double logging
        logger.propagate = False

        # Stream handler for console output
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

        # Suppress py4j logger to reduce noise (pyspark related)
        logging.getLogger("py4j").setLevel(logging.WARNING)

        return logger


# eom
