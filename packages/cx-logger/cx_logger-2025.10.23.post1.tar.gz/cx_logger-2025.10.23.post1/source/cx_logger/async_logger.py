from .levels import levels
from .handler import handler
from .logger import logger

class async_logger(logger):
    """
    That is logger, which use async methods to save data into handles.

    Methods
    -------
    async info(content, *args, **kwargs)
        That log info level message.

    async warning(content, *args, **kwargs)
        That log warning level message.

    async error(content, *args, **kwargs)
        That log error level message.

    async critical(content, *args, **kwargs)
        That log critical level message.

    async log(level, content, *args, **kwargs)
        That generally save content to log with given level.
    """

    async def info(self, content: str, *args, **kwargs) -> None:
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

        await self.log(levels.info, content, *args, **kwargs)

    async def warning(self, content: str, *args, **kwargs) -> None:
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

        await self.log(levels.warning, content, *args, **kwargs)

    async def error(self, content: str, *args, **kwargs) -> None:
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

        await self.log(levels.error, content, *args, **kwargs)

    async def critical(self, content: str, *args, **kwargs) -> None:
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

        await self.log(levels.critical, content, *args, **kwargs)

    async def log(self, level: levels, content: str, *args, **kwargs) -> None:
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
        
        await self._write_to_all(
            self._get_message(level, content, *args, **kwargs)
        )
    
    async def _write_to_all(self, content: str) -> None:
        """
        That write content to all handlers.

        Parameters
        ----------
        content : str
            Content to been writen.
        """

        for handler in self._get_handlers():
            await handler.adding(content) 


