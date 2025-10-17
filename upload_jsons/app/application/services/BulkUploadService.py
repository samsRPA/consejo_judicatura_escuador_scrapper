

from pathlib import Path
from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.CargaMasivaCJRepository import CargaMasivaCJRepository
import os
import json
from datetime import datetime
import math  
import logging

class BulkUploadService(IBulkUploadService):
    logger = logging.getLogger(__name__)

    def __init__( self, db: IDataBase, repository:CargaMasivaCJRepository):
        self.db= db
        self.repository = repository
        

    def carga_masiva(self):
        """
        Busca la carpeta con la fecha actual dentro de output/jsons,
        lee los archivos JSON y ejecuta el procedimiento de cargue masivo.
        Además, limpia los datos de 'CJ_ACTORES' y sobrescribe el JSON limpio.
        """
        conn = None
        try:
            today = datetime.now().strftime("%d-%m-%Y")
            base_dir = Path("/app/output")
            base_path = os.path.join(base_dir, "jsons", today)

            if not os.path.exists(base_path):
                raise FileNotFoundError(f"No existe carpeta para la fecha: {base_path}")

            resultados = {}

            archivos = {
                "CJ_ECUADOR": "actuaciones.json",
                "CJ_ACTORES": "sujetos.json"
            }

            conn = self.db.acquire_connection()

            for tipo, filename in archivos.items():
                file_path = os.path.join(base_path, filename)

                if not os.path.exists(file_path):
                    resultados[tipo] = f"Archivo no encontrado: {file_path}"
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    json_content = json.load(f)

                # 🧹 Limpieza solo para SUJETOS
                if tipo == "CJ_ACTORES":
                    cleaned_data = []
                    for item in json_content:
                        if "idJudicatura" in item:
                            value = item["idJudicatura"]
                            if value is None or (isinstance(value, float) and math.isnan(value)):
                                del item["idJudicatura"]
                        cleaned_data.append(item)

                    # Guardar el JSON limpio sobre el archivo original
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

                    self.logger.info(f"🧽 Archivo limpiado y actualizado: {file_path}")
                    json_content = json.dumps(cleaned_data, ensure_ascii=False)
                else:
                    json_content = json.dumps(json_content, ensure_ascii=False)

                #Insertar usando el repositorio
                insertado = self.repository.insert_masivo(conn, tipo, json_content)
                if insertado:
                    self.logger.info(f"✅ Insert masivo exitoso para {tipo}")
                    try:
                        #os.remove(file_path)
                        self.logger.info(f"🗑️ Archivo eliminado: {file_path}")
                    except Exception as delete_err:
                        self.logger.warning(f"⚠️ No se pudo eliminar el archivo {file_path}: {delete_err}")
                else:
                    self.logger.error(f"❌ Falló inserción para {tipo}")

            return resultados

        except Exception as e:
            self.logger.error(f"❌ Error inesperado en carga_masiva: {e}")

        finally:
            if conn:
                self.db.release_connection(conn)
