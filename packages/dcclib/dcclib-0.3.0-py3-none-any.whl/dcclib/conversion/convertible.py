from abc import ABC, abstractmethod


class Convertible(ABC):  # pragma: no cover
    """
    Abstract base class for classes that can be converted.
    """

    @abstractmethod
    def convert(self):
        """
        Convert the object.
        """
        pass
