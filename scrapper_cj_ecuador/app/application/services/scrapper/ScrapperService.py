from app.application.dto.ScrapperRequest import ScrapperRequest
from app.domain.interfaces.IScrapperService import IScrapperService
from app.domain.interfaces.IGetDataService import IGetDataService
from app.domain.interfaces.IProcessDataService import IProcessDataService
import logging
from app.application.dto.HoyPathsDto import HoyPathsDto
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService
import json
from pathlib import Path
class ScrapperService(IScrapperService):

    def __init__(self, getData: IGetDataService, processData: IProcessDataService,publish_actuaciones:IActuacionesPublishService, body: ScrapperRequest):
        self.getData = getData
        self.processData = processData
        self.publish_actuaciones= publish_actuaciones
        self.body = body
       

    async def scrapper(self,radicado):
        try:
            paths = HoyPathsDto.build().model_dump()
            movimientos = self.getData.get_incidente_judicatura(radicado,paths["json_dir"])

            actuaciones_globales = []
            for movimiento in movimientos:
                actuaciones = self.getData.get_actuaciones_judiciales(
                    movimiento["idMovimientoJuicioIncidente"],
                    radicado,
                    movimiento["idJudicatura"],
                    movimiento["idIncidenteJudicatura"],
                    movimiento["nombreJudicatura"],
                    movimiento["incidente"]
                )
                actuaciones_globales.extend(actuaciones)

            
            actuaciones_procesadas = self.processData.procesar_actuaciones_judiciales(actuaciones_globales, paths["json_dir"])
            #descargar_actuacion_anexo(actuacion["fecha"], actuacion["radicado"], actuacion["consecutivo"], actuacion["uuid"], actuacion["idJudicatura"],"actuaciones")
            list_uuid_fecha=[]
            for actuacion_procesada in actuaciones_procesadas:
                uuid_actual = actuacion_procesada["uuid"]
                radicado= actuacion_procesada["radicado"]
                fecha= actuacion_procesada["fecha"]

                # ✅ Validación de UUID vacío
                if not uuid_actual:
                    logging.warning(f"⚠️ Actuación en fecha {actuacion_procesada.get('fecha')} llegó SIN uuid, se ignora.")
                    continue  # no lo procesamos

                
                actuacion_descargar={
                    "uuid":uuid_actual,
                    "fecha": fecha,
                    "radicado":  radicado
                    }
                list_uuid_fecha.append(actuacion_descargar)
                anexo = self.getData.get_anexos( fecha, uuid_actual, actuacion_procesada["ieTablaReferencia"],
                                actuacion_procesada["codigo"], actuacion_procesada["idMovimientoJuicioIncidente"] ,actuacion_procesada["tipo"], radicado)
                if anexo:
                    list_uuid_fecha.extend(anexo)
                    
            uuid_con_documentos= self.processData.procesar_uuid_con_documentos(list_uuid_fecha)
            actuaciones_consecutivo= self.processData.procesar_consecutivos(uuid_con_documentos)

            
            await self.publish_actuaciones.publish_actuaciones_download(actuaciones_consecutivo)
        except Exception as e:
            raise e
 

    async def runScrapper(self):
        
        try:
            # Construir el DTO que espera run_multi
            radicado= ScrapperRequest(
                radicado=self.body.radicado,
            )
            
            await self.scrapper(radicado.radicado)

        except Exception as e:
            raise e
       
