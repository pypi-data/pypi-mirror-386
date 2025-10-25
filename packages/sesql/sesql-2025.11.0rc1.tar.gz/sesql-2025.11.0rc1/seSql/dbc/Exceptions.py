
class JDBCSecureConnection(Exception):
    """Custom exception for JDBC secure connection errors.

    This class represents an exception that is raised when there is an issue
    with a JDBC secure connection. It is used to encapsulate specific error
    messages related to JDBC secure connection failures.

    Attributes:
        message (str): The error message describing the issue with the
            JDBC secure connection.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class JDBCConnection(Exception):
    """
    Represents an exception for JDBC connection errors.

    This class provides a custom exception to handle errors related to JDBC
    connections. It stores an error message and enables displaying this message
    when the exception is raised.

    Attributes:
        message (str): The error message associated with the JDBC connection
            exception.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class JDBCLoginFailed(Exception):
    """
    Exception raised for JDBC login failures.

    This exception is used to signal that a login attempt to a JDBC
    data source has failed. It encapsulates a message that provides
    information about the login failure. This class is intended to be
    used in contexts where JDBC authentication errors need to be
    handled explicitly.

    Attributes:
        message (str): Description of the login failure error.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class JDBCConnectionTimeOut(Exception):
    """Exception raised for JDBC connection timeouts.

    This custom exception is used to indicate that a timeout occurred
    while attempting to establish a connection with a JDBC data source.

    Attributes:
        message (str): Error message describing the details of the timeout.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class JDBCConnectionReset(Exception):
    """
    Represents a custom exception for resetting JDBC connections.

    This exception is intended to be raised when there is a need to reset a JDBC
    connection. It allows for providing a message that describes the reason for
    the reset. Typically used in scenarios involving database connection handling
    where a connection reset is required due to errors or connection issues.

    Attributes:
        message (str): The error message describing the reason for the connection
        reset.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class JDBCSQLServerDriver(Exception):
    """
    Custom exception for JDBC SQL Server Driver-related errors.

    This exception is specifically designed to encapsulate errors
    related to the JDBC SQL Server Driver, providing a more descriptive
    and structured way to handle such issues in the codebase.

    Attributes:
        message (str): Detailed error message related to the exception.
    """
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class ODBCLoginFailed(Exception):
    """Exception raised for Login failed for user/pw"""
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class ODBCInvalidOperation(Exception):
    """Exception raised for Trust setting"""
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class ODBCDriverError(Exception):
    """Exception raised for anything not caught by ODBC driver"""
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class SQLQueryException(Exception):
    """Exception raised for anything caught by an SQL query."""
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)


class SQLConnectionException(Exception):
    """Exception raised for anything caught by an SQL query."""
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return str(self.message)
