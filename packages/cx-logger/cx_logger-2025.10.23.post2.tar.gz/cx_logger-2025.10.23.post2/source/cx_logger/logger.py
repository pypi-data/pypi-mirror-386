import time

from .handler import handler
from .levels import levels 

class logger:
    """
    That class is responsible for managing log handlers, and generating
    log message. That formats log messages by adding time, date and also
    level of the message.
    """

    def __init__(self) -> None:
        """
        That initialize handlers set.
        """

        self.__handlers = set()

    def _get_handlers(self) -> tuple:   
        """
        That returns copy of the handlers list.
        """

        return tuple(self.__handlers)

    def _get_message(
        self, 
        level: levels, 
        content: str, 
        *args, 
        **kwargs
    ) -> str:
        """
        That try to format log message. It require level of the message and 
        also message itself. When it get only level and message itself, that
        only add message to level and timestamp info. When more parameters
        had been given that run format function on the first message. It is
        useable when log message must contain for example IP address or
        other things like that.

        Parameters
        ----------
        level : levels
            Log level of the message.

        content : str
            Content of the message to log.
        
        *args, **kwargs
            Optional arguments used when format would be used.

        Returns
        -------
        str
            Result message which would be saved in the logs.
        """

        if len(args) > 0 or len(kwargs) > 0:
            content = content.format(*args, **kwargs)

        return ( \
            self.__level_name(level) + " " + \
            self.time_stamp + " " + \
            content \
        )

    @property
    def time_stamp(self) -> str:
        """
        That return current time as timestamp to use in log message.

        Returns
        -------
        str
            Current time as timestamp.
        """

        return "(" + time.strftime("%Y-%m-%d %H:%M:%S") + ")"

    def __level_name(self, level: levels) -> str:
        """
        That convert level enum value into level stamp.

        Parameters
        ----------
        level : levels
            Level enum to convert.

        Returns
        -------
        str
            Result as string stamp.
        """

        name = ""

        if level == levels.info:
            name = "info"

        if level == levels.warning:
            name = "warning"

        if level == levels.error:
            name = "error"

        if level == levels.critical:
            name = "CRITICAL"

        return ("[" + name + "]")

    def use_handler(self, target: handler) -> object:
        """
        That add new handler to the handlers set.

        Parameters
        ----------
        target : handler
            New handler to add.
        
        Returns
        -------
            Self to chain loading.
        """

        self.__handlers.add(target)
        return self


