from abc import ABC, abstractmethod


class IRadicadosCJService(ABC):

    @abstractmethod
    async def getAllRadicadosCJ(self):
        pass

  
    @abstractmethod
    async def publishRadicadosCJ(self):
        pass
