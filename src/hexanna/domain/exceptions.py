class HexannaDomainException(Exception):
    """Base domain exception for Hexanna IIVX."""
    pass

class OOMRiskExceededException(HexannaDomainException):
    """Raised when an operation threatens host system memory limits."""
    pass

class SandboxedToolViolation(HexannaDomainException):
    """Raised when an unwhitelisted or destructive action is requested."""
    pass
