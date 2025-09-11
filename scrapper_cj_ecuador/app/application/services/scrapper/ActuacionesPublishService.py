
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
import logging
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService


class ActuacionesPublishService(IActuacionesPublishService):
    def __init__(self,producer: IRabbitMQProducer ):
        self.producer=producer
    
    async def publish_actuaciones_download(self,actuaciones):
       
        if not actuaciones:
            raise ValueError("No hay actuaciones para publicar")

        for actuacion in actuaciones:
            try:
                await self.producer.publishMessage(actuacion)
            except Exception as error:
                logging.exception(f"Error al publicar el actuacion: {actuacion}")
                raise error 