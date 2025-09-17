

from pathlib import Path
from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.CargaMasivaCJRepository import CargaMasivaCJRepository
import os
import json
from datetime import datetime

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
        """
        try:
            # Fecha actual en formato YYYY-MM-DD
            today = datetime.now().strftime("%d-%m-%Y")
            base_dir = Path("/app/output")
            base_path = os.path.join(base_dir, "jsons", today)

            if not os.path.exists(base_path):
                raise FileNotFoundError(f"No existe carpeta para la fecha: {base_path}")

            resultados = {}

            # Archivos que esperas cargar
            archivos = {
                "CJ_ECUADOR": "actuaciones.json",
                "CJ_ACTORES": "sujetos.json"
            }

            with self.db.acquire_connection() as conn:
                for tipo, filename in archivos.items():
                    file_path = os.path.join(base_path, filename)

                    if not os.path.exists(file_path):
                        resultados[tipo] = f"Archivo no encontrado: {file_path}"
                        continue

                    with open(file_path, "r", encoding="utf-8") as f:
                        json_content = f.read()

                    # Insertar usando el repositorio
                    insertado = self.repository.insert_masivo(conn, tipo, json_content)
                    if insertado:
                        self.logger.info(f"✅ insert masivo ")
                    else:
                        self.logger.error("❌ no se inserto:")
            return resultados

        except Exception as e:
            self.logger.error(f"❌ Error inesperado: {e}")
        
        
    