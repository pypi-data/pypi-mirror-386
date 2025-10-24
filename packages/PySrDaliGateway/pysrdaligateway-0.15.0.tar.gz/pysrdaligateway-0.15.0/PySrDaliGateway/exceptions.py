"""Custom exceptions for DALI Gateway operations"""


class DaliGatewayError(Exception):
    """Base exception for DALI Gateway operations"""

    def __init__(self, message: str, gw_sn: str | None = None):
        super().__init__(message)
        self.gw_sn = gw_sn
