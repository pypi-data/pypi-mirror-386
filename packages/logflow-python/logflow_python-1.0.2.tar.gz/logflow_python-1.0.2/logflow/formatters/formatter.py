from abc import ABC, abstractmethod
from ..models import Log

class Formatter(ABC):
    @abstractmethod
    def format(self, log: Log):
        pass