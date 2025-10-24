import enum

class levels(enum.Enum):
    """
    That enum store log levels to use.
    """

    """ Info about any action. """
    info = 0
    
    """ Simple warning. """
    warning = 1

    """ Not critical error. """
    error = 2

    """ Critical error. """
    critical = 3



