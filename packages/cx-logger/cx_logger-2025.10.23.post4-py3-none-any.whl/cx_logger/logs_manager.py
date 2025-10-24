import pathlib
import time
import typing

from .file_handler import file_handler
from .async_logger import async_logger
from .sync_logger import sync_logger
from .logger import logger

class logs_manager:
    def __init__(self, target: pathlib.Path | None = None) -> None:
        """
        That create new logs manager. It require directory, where logs would
        be stored.

        Parameters
        ----------
        target : pathlib.Path
        """

        if target is None:
            target = pathlib.Path("./logs")

        if not target.is_dir():
            target.mkdir()

        self.__root = target

    @staticmethod
    def _ends_with(name: str, ending: str) -> bool:
        """
        That check name, and returh True when ends with ending.

        Parameters
        ----------
        name : str
            Name to check.

        ending : str
            Ending to check that name ends with.

        Returns
        -------
        bool   
            True when name ends with ending.
        """

        return name[-len(ending):] == ending

    @property
    def root(self) -> pathlib.Path:
        """
        Logs directory.
        """

        return self.__root

    @property
    def logs(self) -> tuple:
        """
        That return tuple with all logs.
        """

        return tuple(self.iter_logs())

    def iter_logs(self) -> typing.Iterator[pathlib.Path]:
        """
        That generator iterate all logs in the log directory.

        Returns
        -------
        typing.Generator[pathlib.Path]
            Log files.
        """

        for count in self.__root.iterdir():
            if self._ends_with(count.name, ".log"):
                yield self.__root / count

    def search_log(self, name: str | None = None) -> tuple:
        """
        That search for log in the logs directory.

        Parameters
        ----------
        name : str | None
            Name to filter logs by. If none, current date.

        Returns
        -------
        tuple
            All logs for given name.
        """

        if name is None:
            name = self._base_name

        logs = self.iter_logs()
        filtered = filter(lambda count: str(count).find(name) != -1, logs)

        return tuple(filtered)

    @property
    def _base_name(self) -> str:
        """
        That return default base name for current date.

        Returns
        -------
        str
            Name for current date.
        """

        return time.strftime("%Y-%m-%d", time.localtime())
    
    def get_new_file(self) -> pathlib.Path:
        """
        That generate new log file handler.

        Returns
        -------
        pathlib.Path
            New file handler.
        """

        base_name = self._base_name
        name_logs = self.search_log(base_name)
        name_count = len(name_logs)

        while True:
            result_name = (
                base_name + "." + \
                str(name_count + 1) + ".log" \
            )

            result_path = self.root / pathlib.Path(result_name)

            if not result_path.exists():
                return result_path
            
            name_count = name_count + 1

    def get_new_handler(self) -> file_handler:
        """
        That return handler to the new file.

        Returns
        -------
        file_handler
            That return new handler to the new log file.
        """

        return file_handler(self.get_new_file())

    def get_logger(self, logger_type : type) -> logger:
        """
        That return new logger that use new log file.

        Parameters
        ----------
        logger_type : type
            Select async_logger or sync_logger.

        Returns
        -------
        logger
            New logger that use new log file
        """

        return logger_type().use_handler(self.get_new_handler()) 
