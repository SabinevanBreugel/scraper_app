from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def start(self):
        pass