from abc import ABC, abstractmethod


class Extractable(ABC):  # pragma: no cover
    """
    Abstract base class for classes that can extract information.
    """

    @abstractmethod
    def extract(self):
        """
        Extract information from the object.
        """
        pass
