from collections import defaultdict

from imxInsights.exceptions import ImxException, exception_handler


class BuildExceptions:
    """
    A class to manage and handle build exceptions.

    ??? info
        This class collects exceptions during the build process, stores them
        in a dictionary indexed by a unique identifier (PUIC), and provides
        a method to handle all collected exceptions.

    Attributes:
        exceptions (DefaultDict[str, List[ImxException]]): A dictionary to store lists of exceptions indexed by PUIC.
    """

    def __init__(self) -> None:
        self.exceptions: defaultdict[str, list[ImxException]] = defaultdict(list)

    def add(self, exception: ImxException, puic: str) -> None:
        """
        Adds an exception to the collection.

        ??? info
            This method checks if an exception with the same message already exists for the given PUIC.
            If not, it adds the exception to the list for that PUIC.

        Args:
            exception (ImxException): The exception to be added.
            puic (str): The unique identifier associated with the exception.
        """

        if puic in self.exceptions:
            if exception.msg not in [msg.msg for msg in self.exceptions[puic]]:
                self.exceptions[puic].append(exception)
        else:
            self.exceptions[puic] = [exception]

    def handle_all(self) -> None:
        """
        Handles all collected exceptions.

        ??? info
            This method iterates over all exceptions stored in the dictionary and processes them
            using the `exception_handler`.

        """

        for exceptions in self.exceptions.values():
            for exception in exceptions:
                exception_handler.handle_exception(exception)
