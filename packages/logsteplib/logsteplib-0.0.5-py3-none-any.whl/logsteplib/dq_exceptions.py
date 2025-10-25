"""
Module defining custom exceptions for Data Quality (DQ) failures.
"""


class DQFail(Exception):
    """Base class for all DQ Fail exceptions."""


class SchemaMismatchAndEmptyFile(DQFail):
    """Exception for schema mismatch and empty file DQ failure."""

    def __init__(self, message="DQ FAIL: SCHEMA MISMATCH AND EMPTY FILE"):
        super().__init__(message)


class SchemaMismatch(DQFail):
    """Exception for schema mismatch DQ failure."""

    def __init__(self, message="DQ FAIL: SCHEMA MISMATCH"):
        super().__init__(message)


class EmptyFile(DQFail):
    """Exception for empty file DQ failure."""

    def __init__(self, message="DQ FAIL: EMPTY FILE"):
        super().__init__(message)


# eom
