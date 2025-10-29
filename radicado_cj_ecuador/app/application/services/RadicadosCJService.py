#from app.application.dto.KeyResponseDto import KeyResponseDto
from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
from app.domain.interfaces.IRadicadosCJService import IRadicadosCJService
#from app.infrastucture.database.repositories.KeyTybaRepository import KeyTybaRepository
import logging
import time
import os
import json
from pathlib import Path
from app.infrastucture.database.repositories.RadicadosCJRepository import RadicadosCJRepository
from app.application.dto.RadicadoResponseDto import RadicadoResponseDto
from app.application.dto.MetricsDto import (
    radicados_service_requests_total,
    radicados_service_errors_total,
    radicados_service_response_time
)
class RadicadosCJService(IRadicadosCJService):
    logger= logging.getLogger(__name__)
    def __init__(self, producer: IRabbitMQProducer, db: IDataBase, repository: RadicadosCJRepository):
        self.producer = producer
        self.db = db
        self.repository = repository
        

    async def getAllRadicadosCJ(self):
        radicados_service_requests_total.inc()
        start_time = time.time()
        conn = await self.db.acquire_connection()
        try:
            radicados = await self.repository.get_radicados_cj(conn)
            # radicados = [
            #     "17985201900326"
            #     ]
            return radicados
        except Exception as error:
            radicados_service_errors_total.inc()
            self.logger.exception(f"Error al traer los radicados: {error}")
            raise  # Para propagar el error si quieres que el controlador lo capture
        finally:
            await self.db.release_connection(conn)
            elapsed_time = time.time() - start_time
            radicados_service_response_time.observe(elapsed_time)


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

    # async def publishRadicadosCJ(self):
    #     radicados = await self.getAllRadicadosCJ()
    #     if not radicados:
    #         raise ValueError("No hay radicados para publicar")

    #     output_dir = Path("/app/output")
    #     output_dir.mkdir(parents=True, exist_ok=True)
    #     output_file = output_dir / "radicados.json"

    #     # Leer contenido previo si existe
    #     if output_file.exists():
    #         with open(output_file, "r", encoding="utf-8") as f:
    #             try:
    #                 radicados_existentes = json.load(f)
    #             except json.JSONDecodeError:
    #                 radicados_existentes = []
    #     else:
    #         radicados_existentes = []

    #     # Convertir lista existente a set de IDs (si los radicados son strings)
    #     radicados_guardados = {r["radicado"] if isinstance(r, dict) and "radicado" in r else r for r in radicados_existentes}

    #     nuevos_radicados = []

    #     for radicado in radicados:
    #         try:
    #             radicado_dto = RadicadoResponseDto(radicado=radicado).model_dump()
    #             radicado_id = radicado_dto.get("radicado")

    #             # Evitar duplicados
    #             if radicado_id not in radicados_guardados:
    #                 radicados_guardados.add(radicado_id)
    #                 nuevos_radicados.append(radicado_dto)

    #             # Publicar mensaje
    #             await self.producer.publishMessage(radicado_dto)

    #         except Exception as error:
    #             self.logger.exception(f"Error al publicar el radicado: {radicado}")
    #             raise error

    #     # Agregar los nuevos radicados al JSON
    #     if nuevos_radicados:
    #         radicados_existentes.extend(nuevos_radicados)
    #         with open(output_file, "w", encoding="utf-8") as f:
    #             json.dump(radicados_existentes, f, ensure_ascii=False, indent=4)

    #         self.logger.info(f"✅ {len(nuevos_radicados)} nuevos radicados guardados en {output_file}")
    #     else:
    #         self.logger.info("ℹ️ No hay radicados nuevos para agregar al JSON.")