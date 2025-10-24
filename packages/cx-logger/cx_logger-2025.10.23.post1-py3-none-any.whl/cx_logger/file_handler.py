import pathlib
import os

from .handler import handler

class file_handler(handler):    
    """
    That handler puts log to file given when object was created.
    """

    def __init__(self, target: pathlib.Path) -> None:
        """
        That initialize new object with given file.

        Parameters
        ----------
        target : pathlib.Path
            File to use by handler.
        """

        super().__init__()

        self.__target = target
        self.__handler = None

    def add(self, content: str) -> None:
        """
        That add new content to the file as new line.

        Parameters
        ----------
        content : str
            Content to add into the file as new line.
        """

        if not self.is_ready:
            self.open()
        
        self.__handler.write(content + os.linesep)

    @property
    def is_ready(self) -> bool: 
        """
        That check that file handler is ready to use or not.
        """

        return self.__handler is not None and not self.__handler.closed

    def open(self) -> None:
        """
        That open file and save handler to use in the future.
        """

        if not self.is_ready:
            self.__handler = self.__target.open("a")

    def clean(self) -> None:
        """
        That close file handler if it is open yet. 
        """

        if not self.is_ready:
            return

        self.__handler.close()


