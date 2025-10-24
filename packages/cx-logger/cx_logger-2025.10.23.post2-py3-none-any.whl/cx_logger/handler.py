import asyncio

class handler:
    """
    That is class, which is used to implements new handlers. Handler is 
    element, which directly store content to log. For example.
    
    To implement property handler, implement:
     * add(str) <- Add new content to log,
     * open() <- Optional function, create creatr handler for add,
     * clean() <- Optional function, clean up resources user by handler.
    """

    def __init__(self) -> None:
        """
        That prepare lock for the hndler.
        """

        self.__lock = asyncio.Lock()
    
    def __del__(self) -> None:
        """
        That clean up handler when item is removed.
        """

        self.clean()

    def open(self) -> None:
        """
        That register system resources for handler.
        """

        pass

    async def adding(self, content: str) -> None:
        """
        That add new content to the the log as new line. It do that 
        asynchronically.
        
        Parameters
        ----------
        content : str
            Content which must be added to log.
        """

        async with self.__lock:
            await asyncio.to_thread(self.add, content)

    def add(self, content: str) -> None:
        """
        That add new content to the log as new line . It is virtual 
        function, and must being overwritten.

        Parameters
        ----------
        content : str
            Content which must be added to log.
        """

        raise NotImplementedError()

    def clean(self) -> None:
        """
        That clean up resources used by handler.
        """

        pass
