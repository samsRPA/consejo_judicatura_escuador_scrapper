#from app.application.dto.KeyResponseDto import KeyResponseDto
from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
from app.domain.interfaces.IRadicadosCJService import IRadicadosCJService
#from app.infrastucture.database.repositories.KeyTybaRepository import KeyTybaRepository
import logging

from app.infrastucture.database.repositories.RadicadosCJRepository import RadicadosCJRepository
from app.application.dto.RadicadoResponseDto import RadicadoResponseDto

class RadicadosCJService(IRadicadosCJService):
    logger= logging.getLogger(__name__)
    def __init__(self, producer: IRabbitMQProducer, db: IDataBase, repository: RadicadosCJRepository):
        self.producer = producer
        self.db = db
        self.repository = repository

    async def getAllRadicadosCJ(self):
        conn = await self.db.acquire_connection()
        try:
            #radicados = await self.repository.get_radicados_cj( conn)
            radicados = [
                "17985201900326",
            ]

            return radicados
        except Exception as error:
            self.logger.exception(f"Error al traer los radicados: {error}" )
        finally:
            await  self.db.release_connection(conn)


    async def publishRadicadosCJ(self):
        radicados = await self.getAllRadicadosCJ()
        if not radicados:
            raise ValueError("No hay radicados para publicar")

        for radicado in radicados:
            try:
                # Convertir cada string en DTO → dict
                radicados_dto = RadicadoResponseDto(radicado=radicado).model_dump()
                
                await self.producer.publishMessage(radicados_dto)
            except Exception as error:
                self.logger.exception(f"Error al publicar el radicado: {radicado}")
                raise error 