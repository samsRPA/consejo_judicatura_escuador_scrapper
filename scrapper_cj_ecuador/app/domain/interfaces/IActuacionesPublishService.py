from abc import ABC, abstractmethod

class IActuacionesPublishService(ABC):

    @abstractmethod
    async def publish_actuaciones_download(self,actuaciones):
        pass
    
