class NoIncomingException(Exception):
    """Thrown when no incoming message is availabl

    Replaced by [almabtrieb.stream.StreamNoNewItemException][]"""

    pass


class ErrorMessageException(Exception):
    """Thrown when an error message is received"""


class UnsupportedMethodException(Exception):
    """Thrown when a method not supported by the backend is called"""
