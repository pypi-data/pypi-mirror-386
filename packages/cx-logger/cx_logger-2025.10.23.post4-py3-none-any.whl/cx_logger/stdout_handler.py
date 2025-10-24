import sys
import os

from .handler import handler

class stdout_handler(handler):
    """
    That handler simple put logs into stdout.
    """

    def add(self, content: str) -> None:
        """
        That put content as new line into stdout.

        Parameters
        ----------
        content : str
            Content to write as new line.
        """

        sys.stdout.write(content + os.linesep)

    
