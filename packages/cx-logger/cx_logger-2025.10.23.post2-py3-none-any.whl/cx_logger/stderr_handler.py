import sys
import os

from .handler import handler

class stderr_handler(handler):
    """
    That handler simple put logs into stderr.
    """

    def add(self, content: str) -> None:
        """
        That put contewnt as new line in stderr.
        
        Parameters
        ----------
        content : str
            Content to write as new line.
        """

        sys.stderr.write(content + os.linesep)



