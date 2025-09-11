from abc import ABC, abstractmethod


class IScrapperService(ABC):

    @abstractmethod
    async def scrapper(self,radicado):
        pass
        
    @abstractmethod
    async def runScrapper(self):
        pass
