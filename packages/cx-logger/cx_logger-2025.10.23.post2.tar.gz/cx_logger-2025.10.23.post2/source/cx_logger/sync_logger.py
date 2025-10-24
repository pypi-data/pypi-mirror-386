from .levels import levels
from .handler import handler
from .logger import logger

class sync_logger(logger):
    """
    That is logger which use standard sync mode..

    Methods
    -------
    info(content, *args, **kwargs)
        That log info level message.

    warning(content, *args, **kwargs)
        That log warning level message.

    error(content, *args, **kwargs)
        That log error level message.

    critical(content, *args, **kwargs)
        That log critical level message.

    log(level, content, *args, **kwargs)
        That generally save content to log with given level.
    """


    def info(self, *args, **kwargs) -> None:
        """
        That log info level message.

        Parameters
        ----------
        content : str
            Content to store in the log.

        *args, **kwargs
            When any of that parameters had been given, then format funcion
            hed been used on the content.
        """
        
        self.log(levels.info, *args, **kwargs)

    def warning(self, *args, **kwargs) -> None:
        """
        That log warning level message.

        Parameters
        ----------
        content : str
            Content to store in the log.

        *args, **kwargs
            When any of that parameters had been given, then format funcion
            hed been used on the content.
        """
        
        self.log(levels.warning, *args, **kwargs)
  
    def error(self, *args, **kwargs) -> None:
        """
        That log error level message.

        Parameters
        ----------
        content : str
            Content to store in the log.

        *args, **kwargs
            When any of that parameters had been given, then format funcion
            hed been used on the content.
        """

        self.log(levels.error, *args, **kwargs)
    
    def critical(self, *args, **kwargs) -> None:
        """
        That log critical level message.

        Parameters
        ----------
        content : str
            Content to store in the log.

        *args, **kwargs
            When any of that parameters had been given, then format funcion
            hed been used on the content.
        """
        
        self.log(levels.critical, *args, **kwargs)

    def log(self, level: levels, *args, **kwargs) -> None:
        """
        That log message, log level is given in the parameter.

        Parameters
        ----------
        level : levels
            Level of the message to save.
        
        content : str
            Content to store in the log.

        *args, **kwargs
            When any of that parameters had been given, then format funcion
            hed been used on the content.
        """

        self._write_to_all(self._get_message(level, *args, **kwargs))

    def _write_to_all(self, content: str) -> None: 
        """
        That write content to all handlers.

        Parameters
        ----------
        content : str
            Content to been writen.
        """

        for handler in self._get_handlers():
            handler.add(content)
