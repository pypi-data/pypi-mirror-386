"""System function enumeration for system telegrams."""

from enum import Enum
from typing import Optional


class SystemFunction(str, Enum):
    """System function codes for system telegrams.

    Attributes:
        NONE: Undefined function.
        DISCOVERY: Discover function.
        READ_DATAPOINT: Read datapoint.
        READ_CONFIG: Read configuration.
        WRITE_CONFIG: Write configuration.
        BLINK: Blink LED function.
        UNBLINK: Unblink LED function.
        DOWNLOAD_MSACTIONTABLE: Download module specific action table.
        DOWNLOAD_ACTIONTABLE: Download ActionTable.
        EOF: End of msactiontable response.
        MSACTIONTABLE: Module specific action table response.
        ACTIONTABLE: Module specific action table response.
        ACK: Acknowledge response.
        NAK: Not acknowledge response.
        UNKNOWN_26: Used after discover, unknown purpose.
        ACTION: Action function.
    """

    NONE = "00"  # Undefined
    DISCOVERY = "01"  # Discover function
    READ_DATAPOINT = "02"  # Read datapoint
    READ_CONFIG = "03"  # Read configuration
    WRITE_CONFIG = "04"  # Write configuration
    BLINK = "05"  # Blink LED function
    UNBLINK = "06"  # Unblink LED function
    DOWNLOAD_MSACTIONTABLE = (
        "13"  # Download the module specific action table (MsActionTable)
    )
    DOWNLOAD_ACTIONTABLE = "11D"  # Download ActionTable
    EOF = "16"  # End of msactiontable response
    MSACTIONTABLE = "17"  # module specific action table (MsActionTable) response
    ACTIONTABLE = "17"  # module specific action table (MsActionTable) response
    ACK = "18"  # Acknowledge response
    NAK = "19"  # Not acknowledge response
    UNKNOWN_26 = "26"  # Used after discover, but don't know what it is
    ACTION = "27"  # Action function

    def get_description(self) -> str:
        """Get the description of the SystemFunction.

        Returns:
            Human-readable description of the function.
        """
        return (
            {
                self.DISCOVERY: "Discover function",
                self.READ_DATAPOINT: "Read datapoint",
                self.READ_CONFIG: "Read configuration",
                self.WRITE_CONFIG: "Write configuration",
                self.BLINK: "Blink LED function",
                self.DOWNLOAD_MSACTIONTABLE: "Download the msactiontable",
                self.DOWNLOAD_ACTIONTABLE: "Download ActionTable",
                self.EOF: "End of msactiontable response",
                self.ACTIONTABLE: "Actiontable response",
                self.MSACTIONTABLE: "Msactiontable response",
                self.UNBLINK: "Unblink LED function",
                self.ACK: "Acknowledge response",
                self.NAK: "Not acknowledge response",
                self.ACTION: "Action function",
            }
        ).get(self, "Unknown function")

    @classmethod
    def from_code(cls, code: str) -> Optional["SystemFunction"]:
        """Get SystemFunction from code string.

        Args:
            code: Function code string.

        Returns:
            SystemFunction instance if found, None otherwise.
        """
        for func in cls:
            if func.value.lower() == code.lower():
                return func
        return None
