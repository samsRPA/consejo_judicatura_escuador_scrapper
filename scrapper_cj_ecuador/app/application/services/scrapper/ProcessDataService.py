import requests
import json
import logging
import os
import html
import pandas as pd
from app.domain.interfaces.IProcessDataService import IProcessDataService

class ProcessDataService(IProcessDataService,):
    def __init__(self):
        pass
    
    def procesar_actuaciones_judiciales(self,data,json_dir,save_file=True):
        try:
            # Normalizar todo en un solo DataFrame
            df = pd.json_normalize(data)

        # Convertir fechas (mantener original con hora y extraer solo la fecha DD-MM-YYYY)
            if "fecha" in df.columns:
                df["fecha_original"] = pd.to_datetime(df["fecha"], errors='coerce')
                df["fecha"] = df["fecha_original"].dt.strftime("%d-%m-%Y")
                df["hora"] = df["fecha_original"].dt.strftime("%H:%M:%S")   # 👉 nueva columna con solo la hora
                    # Crear campo FECHA_REGISTRO_TYBA = fecha-hora
                df["FECHA_REGISTRO_TYBA"] = df["fecha"] + "-" + df["hora"]
    
            # Columnas extra
            df = df.assign(
            
                cod_despacho_rama=df.get("nombreJudicatura",0),
                actuacion_rama=df.get("tipo", "").str.strip(),
                anotacion_rama = (
                    df.get("actividad", "")
                    .str.replace(r"<[^>]*>", "", regex=True)   # quitar etiquetas HTML
                    .apply(lambda x: html.unescape(x))         # decodificar entidades HTML (&eacute; → é)
                    .str.strip()                               # quitar espacios al inicio y final
                    .str.upper()                               # pasar a mayúsculas
                ),
                origen_datos="CJ_ECUADOR",
                #radicado = df.get("idJuicio", "").str.strip().str[:5] + "-" + df.get("idJuicio", "").str.strip().str[5:9] + "-" + df.get("idJuicio", "").str.strip().str[9:],
                radicado= df.get("idJuicio", "").str.strip(),
                idJudicatura=df.get("idJudicatura", "").str.strip(),
                idIncidenteJudicatura=df.get("idIncidenteJudicatura", ""),  
                incidente=df.get("incident",0),
                uuid= df.get("uuid")
            )
                        
            # ❌ Eliminar la columna auxiliar
            df = df.drop(columns=["fecha_original"])

            # 👉 Retornar todo
            actuaciones_completo = df.to_dict(orient="records")
           
            # 👉 Retornar simplificado
            actuaciones_guardar = df[[
                "radicado",
                "cod_despacho_rama",
                "fecha",
                "actuacion_rama",
                "anotacion_rama",
                "origen_datos",
                "FECHA_REGISTRO_TYBA",
            # "consecutivo"
            ]].to_dict(orient="records")

           # Guardar archivo sin duplicados
            if save_file:
                output_file = json_dir / "actuaciones.json"
                if os.path.exists(output_file):
                    try:
                        with open(output_file, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
                else:
                    existing_data = []

                # Crear set de llaves únicas de lo ya existente
                existing_keys = {
                    (d["radicado"], d["fecha"], d["actuacion_rama"], d["anotacion_rama"])
                    for d in existing_data
                }

                # Filtrar solo los registros nuevos
                new_unique_data = [
                    d for d in actuaciones_guardar
                    if (d["radicado"], d["fecha"], d["actuacion_rama"], d["anotacion_rama"]) not in existing_keys
                ]

                if new_unique_data:
                    existing_data.extend(new_unique_data)
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(existing_data, f, ensure_ascii=False, indent=4)
                    logging.info(f"✅ {len(new_unique_data)} actuaciones nuevas guardadas en {output_file}")
                else:
                    logging.info("⚠️ No se guardaron actuaciones, todas ya existían.")

            return actuaciones_completo

        except Exception as e:
            logging.error(f"❌ Error inesperado: {e}")
            return []


    def procesar_uuid_con_documentos(self,lista):
        """
        Filtra una lista de diccionarios (cada uno con clave 'uuid')
        y retorna solo los que tienen un link válido con documentos (PDF).
        """
        nueva_lista = []

        for fila in lista:
            uuid = fila.get("uuid")
            if not uuid:
                logging.warning("⚠️ Fila sin UUID, se omite")
                continue

            url = f"https://api.funcionjudicial.gob.ec/CJ-DOCUMENTO-SERVICE/api/document/query/hba?code={uuid}"
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()

                content_type = resp.headers.get("Content-Type", "").lower()
                if "pdf" in content_type:
                    logging.warning(f"✅  [{uuid}] Cuenta con documento valido.  Content-Type: {content_type}")
                    nueva_lista.append(fila)  # ✅ solo los válidos
                else:
                    logging.warning(f"⚠️ [{uuid}] No es un PDF válido o la actuación no tiene documentos. Content-Type: {content_type}")

            except requests.RequestException as e:
                logging.error(f"❌ Error al validar UUID {uuid}: {e}")

        return nueva_lista
        
    def procesar_consecutivos(self,data):
        """
        Procesa la data (lista de diccionarios o DataFrame) 
        y retorna una lista de diccionarios con la info lista
        para descargar los PDFs. 
        Omite registros donde 'uuid' sea 'NV'.
        """
        # Normalizar a DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        # Calcular consecutivo por fecha
        df["consecutivo"] = df.groupby("fecha").cumcount() + 1

        # Crear JSON/lista de diccionarios con los datos listos
        actuaciones = df.to_dict(orient="records")
        return actuaciones



