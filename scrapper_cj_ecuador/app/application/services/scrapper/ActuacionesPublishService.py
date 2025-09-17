
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
import logging
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService


class ActuacionesPublishService(IActuacionesPublishService):
    logger= logging.getLogger(__name__)
    def __init__(self,producer: IRabbitMQProducer ):
        self.producer=producer
    
    async def publish_actuaciones_download(self,actuaciones):
       
        if not actuaciones:
            raise ValueError("No hay actuaciones para publicar")

        for actuacion in actuaciones:
            try:
                await self.producer.publishMessage(actuacion)
            except Exception as error:
                self.logger.exception(f"Error al publicar el actuacion: {actuacion}")
                raise error 