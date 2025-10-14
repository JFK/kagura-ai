"""Compression-related exceptions"""


class CompressionError(Exception):
    """Base exception for compression errors"""

    pass


class TokenCountError(CompressionError):
    """Error during token counting"""

    pass


class ModelNotSupportedError(CompressionError):
    """Model is not supported"""

    pass
