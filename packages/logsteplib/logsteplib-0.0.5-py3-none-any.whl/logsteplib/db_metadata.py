"""
Data quality metadata structure for logging and future database persistence.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class DQMetadata:
    """
    A data structure representing metadata for data quality tracking.

    This class encapsulates information about a file and its processing status, including user details, file attributes,
    and rejection reasons if applicable. It is designed to support logging, auditing, and future persistence to a
    database.
    """

    target: str
    key: str
    input_file_name: str
    file_name: str
    user_name: str
    user_email: str
    modify_date: str  # Consider using datetime for stricter typing
    file_size: int
    file_row_count: int
    status: str
    rejection_reason: Optional[str] = None
    file_web_url: Optional[str] = None

    def to_json(self) -> str:
        """
        Convert the metadata instance to a JSON-formatted string.

        This method serialises the metadata fields into a human-readable JSON string, suitable for logging,
        transmission, or storage.

        Returns:
            str: A JSON representation of the metadata.
        """
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# eom
