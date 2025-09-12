from pathlib import Path
import requests
import json
import logging
import os

from app.domain.interfaces.IGetDataService import IGetDataService
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter



import pandas as pd

class GetDataService(IGetDataService):
    
    def __init__(self):
        pass
    
    def get_incidente_judicatura(self, radicado: str, json_dir: Path):
        url = f"https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-CLEX-SERVICE/api/consulta-causas-clex/informacion/getIncidenteJudicatura/{radicado}"
        
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or len(data) == 0:
                return {"success": False, "error": "No se encontró información en la respuesta"}

            # ---------------- Normalizamos actores ----------------
            actores = pd.json_normalize(
                data,
                record_path=["lstIncidenteJudicatura", "lstLitiganteActor"],
                meta=["idJudicatura"],
                errors="ignore"
            )
            if not actores.empty:
                actores = actores.assign(
                  # RADICADO=f"{radicado[:5]}-{radicado[5:9]}-{radicado[9:]}",
                    RADICADO=radicado,
                    TIPO_SUJETO="ACTOR",
                    NOMBRE_ACTOR=actores["nombresLitigante"],
                    ORIGEN_DATOS="CJ_ECUADOR"
                )[["RADICADO", "TIPO_SUJETO", "NOMBRE_ACTOR", "ORIGEN_DATOS"]]

            # ---------------- Normalizamos demandados ----------------
            demandados = pd.json_normalize(
                data,
                record_path=["lstIncidenteJudicatura", "lstLitiganteDemandado"],
                meta=["idJudicatura"],
                errors="ignore"
            )
            if not demandados.empty:
                demandados = demandados.groupby("idJudicatura").agg({
                    "nombresLitigante": lambda x: list(x)
                }).reset_index()

                demandados = demandados.assign(
                    #RADICADO=f"{radicado[:5]}-{radicado[5:9]}-{radicado[9:]}",
                    RADICADO=radicado,
                    TIPO_SUJETO="DEMANDADO",
                    NOMBRE_ACTOR=demandados["nombresLitigante"],
                    ORIGEN_DATOS="CJ_ECUADOR"
                )[["RADICADO", "TIPO_SUJETO", "NOMBRE_ACTOR", "ORIGEN_DATOS"]]

            # ---------------- Concatenar actores + demandados ----------------
            sujetos = pd.concat([actores, demandados], ignore_index=True)
            sujetos_list = sujetos.to_dict(orient="records")

            # ---------------- Guardar sin duplicados ----------------
            output_file: str = json_dir / "sujetos.json"

            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []

            # Llaves únicas de lo que ya existe
            existing_keys = {
                (d["RADICADO"], d["TIPO_SUJETO"], str(d["NOMBRE_ACTOR"]), d["ORIGEN_DATOS"])
                for d in existing_data
            }

            # Filtrar solo los que no están ya en el archivo
            new_unique_data = [
                d for d in sujetos_list
                if (d["RADICADO"], d["TIPO_SUJETO"], str(d["NOMBRE_ACTOR"]), d["ORIGEN_DATOS"]) not in existing_keys
            ]

            if new_unique_data:
                existing_data.extend(new_unique_data)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)

                logging.info(f"✅ {len(new_unique_data)} registros nuevos agregados en {output_file}")
            else:
                logging.info("⚠️ No se agregaron registros, todos ya existían.")

            # ---------------- Normalizamos incidente principal ----------------
            df = pd.json_normalize(
                data,
                record_path="lstIncidenteJudicatura",
                meta=["idJudicatura", "nombreJudicatura"],
                errors="ignore"
            )
            columnas = [
                "idMovimientoJuicioIncidente",
                "idJudicatura",
                "idIncidenteJudicatura",
                "nombreJudicatura",
                "incidente",
            ]

            df = df[columnas].copy()
            df["radicado"] = radicado

            return df.to_dict(orient="records")

        except requests.exceptions.Timeout:
            logging.error("⏳ La petición tardó demasiado en responder")
            return {"success": False, "error": "Timeout en la petición"}
        except requests.exceptions.HTTPError as e:
            logging.error(f"⚠️ Error HTTP: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error en la petición: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logging.error(f"🔥 Error inesperado: {str(e)}")
            return {"success": False, "error": str(e)}


    def get_actuaciones_judiciales(self,idMovimientoJuicioIncidente, radicado, id_judicatura,
                                idIncidenteJudicatura, nombreJudicatura, incidente):
        
        url = "https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-SERVICE/api/consulta-causas/informacion/actuacionesJudiciales"
        payload = {
            "idMovimientoJuicioIncidente": idMovimientoJuicioIncidente,
            "idJuicio": radicado,
            "idJudicatura": str(id_judicatura),
            "idIncidenteJudicatura": idIncidenteJudicatura,
            "aplicativo": "web",
            "nombreJudicatura": nombreJudicatura,
            "incidente": incidente
        }

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500,502,503,504],
            allowed_methods=["POST"]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            response = session.post(url, json=payload, timeout=(3, 10))
            response.raise_for_status()
            data = response.json()
           
            
            if not isinstance(data, list) or len(data) == 0:
                logging.warning("⚠️ Respuesta vacía o no es lista")
                data = []
            # Si data es una lista de dicts, agregamos los nuevos campos a cada objeto
            data_completa= [
                {
                    **item,
                    "idIncidenteJudicatura": idIncidenteJudicatura,
                    "nombreJudicatura": nombreJudicatura,
                    "incidente": incidente
                }
                for item in data
            ]

            return data_completa

        except requests.exceptions.Timeout:
            logging.error("⏳ Timeout en la solicitud")
            return []
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔌 Error de conexión: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            logging.error(f"🌐 Error HTTP {response.status_code}: {e}")
            return []
        except Exception as e:
            logging.error(f"❌ Error inesperado: {e}")
            return []


    def get_anexos(self,actuacion_procesada):

        
        fecha= actuacion_procesada["fecha"]
        uuid_actuacion=actuacion_procesada["uuid"] 
        ieTablaReferencia=actuacion_procesada["ieTablaReferencia"]
        codigo=actuacion_procesada["codigo"]
        idMovimientoJuicioIncidente=actuacion_procesada["idMovimientoJuicioIncidente"]
        tipo=actuacion_procesada["tipo"]
        radicado=actuacion_procesada["radicado"]
        hora=actuacion_procesada["hora"]
        cod_despacho_rama=actuacion_procesada["cod_despacho_rama"]
        actuacion_rama=actuacion_procesada["actuacion_rama"]
        anotacion_rama=actuacion_procesada["anotacion_rama"]
        origen_datos=actuacion_procesada["origen_datos"]
        fecha_registro_tyba=actuacion_procesada["FECHA_REGISTRO_TYBA"]
        
        
        url = "https://api.funcionjudicial.gob.ec/EXPEL-CONSULTA-CAUSAS-CLEX-SERVICE/api/consulta-causas-clex/datos/anexos"

        payload = {
            "TablaReferencia": ieTablaReferencia,
            "IdTablaReferencia": codigo,
            "IdIndiceElectronico": 0,
            "idmovimientojuicioincidente": idMovimientoJuicioIncidente,
            "tipoActuacion": tipo
        }

        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504, 404],
            allowed_methods=["POST"]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            response = session.post(url, json=payload, timeout=(5, 15))
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                logging.error("❌ La respuesta no es un JSON válido")
                return []

            if not isinstance(data, list):
                logging.warning("⚠️ La respuesta no fue una lista. Contenido inesperado.")
                return []

            if not data:
                logging.info(f"ℹ️ No se encontraron anexos para la actuación con uuid: {uuid_actuacion}, del radicado:{radicado}")
                return []

            # Normalizar la respuesta
            df = pd.json_normalize(data)

            if "UUID" not in df.columns:
                logging.warning("⚠️ No se encontró ningún UUID en los anexos.")
                return []

            # Renombrar a minúscula
            df = df.rename(columns={"UUID": "uuid"})
            
                        
            # Filtrar anexos con UUID válido
            df = df[df["uuid"].notna() & (df["uuid"].str.strip() != "")]

            if df.empty:
                logging.info(f"ℹ️ Todos los anexos para la actuación con uuid: {uuid_actuacion} y radicado {radicado} tenían UUID vacío")
                return []

            # ✅ Solo quedarme con la columna uuid
            df = df[["uuid"]]

            # ✅ Agregar todas las variables fijas de la actuación original
            df["fecha"] = fecha
            df["radicado"] = radicado
            df["hora"] = hora
            df["cod_despacho_rama"] = cod_despacho_rama
            df["actuacion_rama"] = actuacion_rama
            df["anotacion_rama"] = anotacion_rama
            df["origen_datos"] = origen_datos
            df["fecha_registro_tyba"] = fecha_registro_tyba

                        

            logging.info(f"✅ Se encontraron {len(df)} anexos válidos para la actuación con uuid: {uuid_actuacion}, del radicado {radicado}")

            # Convertir a lista de dicts con TODOS los campos
            anexos = df.to_dict(orient="records")
            return anexos

        except requests.RequestException as e:
            logging.error(f"❌ Error en la solicitud de anexos: {e}")
            return []
        except requests.exceptions.Timeout:
            logging.error("⏳ La solicitud excedió el tiempo de espera")
            return []
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔌 Error de conexión: {str(e)}")
            return []
        except requests.exceptions.HTTPError as e:
            logging.error(f"🌐 Error HTTP {response.status_code}: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"❌ Error inesperado: {str(e)}")
            return []

