from app.application.dto.ScrapperRequest import ScrapperRequest
from app.domain.interfaces.IScrapperService import IScrapperService
from app.domain.interfaces.IGetDataService import IGetDataService
from app.domain.interfaces.IProcessDataService import IProcessDataService
import logging
from app.application.dto.HoyPathsDto import HoyPathsDto
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService

from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.RadicadoProcesadoCJRepository import RadicadoProcesadoCJRepository

class ScrapperService(IScrapperService):

    logger= logging.getLogger(__name__)
  
    def __init__(self,db: IDataBase,repository:RadicadoProcesadoCJRepository, getData: IGetDataService, processData: IProcessDataService,publish_actuaciones:IActuacionesPublishService,body: ScrapperRequest):
        self.db=db
        self.repository=repository
        self.getData = getData
        self.processData = processData
        self.publish_actuaciones= publish_actuaciones
        self.body = body
       

    async def scrapper(self,radicado):
        try:
            conn = await self.db.acquire_connection()
            
            paths = HoyPathsDto.build().model_dump()
            
            is_radicado_procesado= await self.repository.radicacion_procesada(conn,radicado)
            
            movimientos = self.getData.get_incidente_judicatura(radicado,paths["json_dir"])
            
            if not movimientos:
            # La lista está vacía, no hay movimientos
                self.logger.warning(f" ⚠️ el radicado {radicado} no tiene movimientos")
                return
            else:
            # Hay uno o más movimientos en la lista
                self.logger.info(f"Hay {len(movimientos)} movimientos para el radicado {radicado}")

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

       
              
            self.logger.info(f"Hay {len(actuaciones_globales)} actuaciones globales para el radicado {radicado}")

            actuaciones_filtradas= self.processData.filtrar_actuaciones_procesadas(actuaciones_globales,is_radicado_procesado)
            if not actuaciones_filtradas:
                self.logger.info(f" 🕳️ No hay actuaciones en los últimos días para el radicado  {radicado}")
                return
      
            actuaciones_procesadas = self.processData.procesar_actuaciones_judiciales( actuaciones_filtradas, paths["json_dir"])

            if not actuaciones_procesadas:
                self.logger.warning(f" No hay actuaciones procesadas para el radicado {radicado}")
                return
            else:
                self.logger.info(f"Hay {len(actuaciones_procesadas)} actuaciones procesadas para el radicado {radicado}")
                
            list_uuid_fecha=[]
            for actuacion_procesada in actuaciones_procesadas:
                uuid_actual = actuacion_procesada["uuid"]
 
            

                # ✅ Validación de UUID vacío
                if not uuid_actual:
                    self.logger.warning(f"⚠️ Actuación en fecha {actuacion_procesada.get('fecha')} llegó SIN uuid, se ignora para el radicado {radicado}.")
                    continue  # no lo procesamos

                actuacion_descargar={
                    "uuid":uuid_actual,
                    "fecha": actuacion_procesada["fecha"],
                    "radicado": actuacion_procesada["radicado"],
                    "cod_despacho_rama":actuacion_procesada["cod_despacho_rama"],
                    "actuacion_rama":actuacion_procesada["actuacion_rama"],
                    "anotacion_rama":actuacion_procesada["anotacion_rama"],
                    "origen_datos":actuacion_procesada["origen_datos"],
                    "fecha_registro_tyba":actuacion_procesada["fecha_registro_tyba"]
                    }
                list_uuid_fecha.append(actuacion_descargar)
                anexo = self.getData.get_anexos(actuacion_procesada)
                if anexo:
                    list_uuid_fecha.extend(anexo)

           
                    
            uuid_con_documentos= self.processData.procesar_uuid_con_documentos(list_uuid_fecha)
            actuaciones_consecutivo= self.processData.procesar_consecutivos(uuid_con_documentos)

            
            await self.publish_actuaciones.publish_actuaciones_download(actuaciones_consecutivo)
        except Exception as e:
            self.logger.error(f"❌ Error : {e}")
            raise e
 

    async def runScrapper(self):
        
        try:
            # Construir el DTO que espera run_multi
            radicado= ScrapperRequest(
                radicado=self.body.radicado,
            )
            
            await self.scrapper(radicado.radicado)

        except Exception as e:
            self.logger.error(f"❌ Error : {e}")
            raise e
       
