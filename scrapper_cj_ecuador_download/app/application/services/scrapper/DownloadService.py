

from app.domain.interfaces.IDownloadService import IDownloadService


import time

import requests
import logging

import os
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories import RadicadosCJRepository
from app.domain.interfaces.IS3Manager import IS3Manager
from app.application.dto.AutosRequestDto import AutosRequestDto
from app.application.dto.HoyPathsDto import HoyPathsDto



class DownloadService(IDownloadService):

    def __init__(self, db: IDataBase, repository:RadicadosCJRepository, S3_manager:IS3Manager, ):
        self.db = db
        self.repository = repository
        self.S3_manager = S3_manager
   
        
        
    async def download_documents(self,fila,actuaciones_dir):
        conn = await self.db.acquire_connection()
        """
        Función que maneja la descarga e inserción de un solo documento.
        Esto se ejecuta en paralelo en varios hilos.
        """
        uuid = fila.uuid
        #   # Ignorar si el uuid es "NV"
        # if uuid == "NV":
        #     logging.info(f"⏭️ Documento ignorado porque el uuid es 'NV' (radicado={radicado_valor}, fecha={fecha_valor}, consecutivo={consecutivo_valor}).")
        #     return None

        
        fecha_valor = fila.fecha
        radicado_valor = fila.radicado
        consecutivo_valor = fila.consecutivo

        
        
        os.makedirs(actuaciones_dir, exist_ok=True)

        nombre_archivo = f"{fecha_valor}_{radicado_valor}_{consecutivo_valor}.pdf"
        ruta_S3 = f"{fecha_valor}_{radicado_valor}_{consecutivo_valor}"
        ruta_pdf = os.path.join(actuaciones_dir, nombre_archivo)

        # Evitar descargas duplicadas en disco
        if os.path.exists(ruta_pdf):
            logging.info(f"⏩ PDF ya existe en disco: {ruta_pdf}")
            return ruta_pdf

        url = f"https://api.funcionjudicial.gob.ec/CJ-DOCUMENTO-SERVICE/api/document/query/hba?code={uuid}"

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "").lower()
            if "pdf" not in content_type:
                logging.warning(f"⚠️ [{uuid}] No es un PDF válido o la actuación no tiene documentos. Content-Type: {content_type}")
                return None
            
            # Verificar si ya existe en BD
            existe = await self.repository.documento_existe(conn, fecha_valor, radicado_valor, consecutivo_valor)
            if existe:
                logging.info(f"📂 [{uuid}] Documento ya existe en la BD (radicado={radicado_valor}, fecha={fecha_valor}, consecutivo={consecutivo_valor}). No se insertará.")
                return None

            # Insertar en BD
            insertado = await self.repository.insertar_documento_simple(
                conn, fecha_valor, radicado_valor, consecutivo_valor, 
                ruta_S3, url, "CJ_ECUADOR", "pdf"
            )

            if insertado:
                with open(ruta_pdf, "wb") as f:
                    f.write(resp.content)
                self.upload_file_s3(ruta_pdf)

                logging.info(f"✅ [{uuid}] PDF descargado, guardado en {ruta_pdf} y registrado en la BD.")
                return ruta_pdf
            else:
                logging.error(f"❌ [{uuid}] No se logró insertar el documento en la BD (radicado={radicado_valor}).")
                return None

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ [{uuid}] Error de red o timeout al descargar: {str(e)}")
            return None
        except Exception as e:
            logging.exception(f"❌ [{uuid}] Error inesperado procesando el documento: {str(e)}")
            return None
       

    def upload_file_s3(self,ruta_pdf):
        subido_s3= self.S3_manager.uploadFile(ruta_pdf)
        if subido_s3:
            logging.info(f"✅ archivo  {ruta_pdf} subido a S3")
            try:
                time.sleep(10)
                os.remove(ruta_pdf)
                logging.info(f"🗑️ Archivo local eliminado: {ruta_pdf}")
            except Exception as e:
                logging.error(f"⚠️ No se pudo eliminar el archivo local {ruta_pdf}: {e}")
        else:
            logging.warning(f"⚠️ Error al subir {ruta_pdf} a S3, se mantiene local.") 

    async def run_download(self,body: AutosRequestDto):
        
        try:
            paths = HoyPathsDto.build().model_dump()
            # Construir el DTO que espera run_multi
            auto= AutosRequestDto(
                uuid=body.uuid,
                fecha=body.fecha,
                radicado=body.radicado,
                consecutivo=body.consecutivo
            )
            
            await self.download_documents(auto,paths["actuaciones_dir"])

        except Exception as e:
            raise e
       

    
    
    # def download_documents_simultaneously(self,actuaciones,actuaciones_dir, max_workers=5):
    #     """
    #     Descarga PDFs en paralelo usando ThreadPoolExecutor.
    #     """
    #     rutas_descargadas = []

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    #         futures = {executor.submit(self.download_documents, fila,actuaciones_dir): fila for fila in actuaciones}

    #         for future in concurrent.futures.as_completed(futures):
    #             result = future.result()
    #             if result:
    #                 rutas_descargadas.append(result)

    #     return rutas_descargadas