
from abc import ABC, abstractmethod

class ICJEcuadorScrapper(ABC):

    @abstractmethod
    async def scrapper(self,radicado):
        pass