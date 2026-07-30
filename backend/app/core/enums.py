import enum


class Role(str, enum.Enum):
    """Access level granted to a user account."""

    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    ACCOUNTING = "ACCOUNTING"


class Status(str, enum.Enum):
    """Lifecycle state of an expense report."""

    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    REFUSED = "REFUSED"
    PROCESSED = "PROCESSED"
