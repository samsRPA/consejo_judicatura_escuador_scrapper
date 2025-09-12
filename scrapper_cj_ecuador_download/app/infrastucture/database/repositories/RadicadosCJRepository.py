import asyncio
import logging

class RadicadosCJRepository:
    def __init__(self, table_car):
        self.table_car = table_car

    async def documento_existe(self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int) -> bool:
        """
        Verifica si existe un documento en la tabla CONTROL_AUTOS_RAMA_1
        según la fecha_notificacion (DD-MM-YYYY), radicacion y consecutivo.
        """
        try:
            query = """
                SELECT 1
                FROM CONTROL_AUTOS_RAMA_1
                WHERE FECHA_NOTIFICACION = TO_DATE(:fecha_notificacion, 'DD-MM-YYYY')
                  AND RADICACION = :radicacion
                  AND CONSECUTIVO = :consecutivo
                  FETCH FIRST 1 ROWS ONLY
            """
            def _execute():
                with conn.cursor() as cursor:
                    cursor.execute(query, {
                        "fecha_notificacion": fecha_notificacion,
                        "radicacion": radicacion,
                        "consecutivo": consecutivo
                    })
                    return cursor.fetchone()

            result = await asyncio.to_thread(_execute)
            return result is not None

        except Exception as error:
            logging.error(f"❌ Error en documento_existe: {error}")
            raise

    async def insertar_actuacion_rama(self, conn,radicado_rama, cod_despacho_rama, fecha_actuacion, actuacion_rama, anotacion_rama, origen_datos,fecha_registro_tyba):
        try:
            query = """
                INSERT INTO ACTUACIONES_RAMA (
                    RADICADO_RAMA,
                    COD_DESPACHO_RAMA,
                    FECHA_ACTUACION,
                    ACTUACION_RAMA,
                    ANOTACION_RAMA,
                    ORIGEN_DATOS,
                    FECHA_REGISTRO_TYBA
                ) VALUES (
                    :radicado_rama,
                    :cod_despacho_rama,
                    TO_DATE(:fecha_actuacion, 'DD-MM-YYYY'),
                    :actuacion_rama,
                    :anotacion_rama,
                    :origen_datos,
                    TO_DATE(:fecha_registro_tyba, 'DD-MM-YYYY-HH24:MI:SS')
                )
            """

            def _execute():
                with conn.cursor() as cursor:
                    cursor.execute(query, {
                        "radicado_rama": radicado_rama,
                        "cod_despacho_rama": cod_despacho_rama,
                        "fecha_actuacion": fecha_actuacion,  # string 'DD-MM-YYYY'
                        "actuacion_rama": actuacion_rama,
                        "anotacion_rama": anotacion_rama,
                        "origen_datos": origen_datos,
                        "fecha_registro_tyba": fecha_registro_tyba  # puede ser None
                    })

            await asyncio.to_thread(_execute)
            await asyncio.to_thread(conn.commit)

            print("✅ Insert en ACTUACIONES_RAMA realizado correctamente")

        except Exception as e:
            print(f"❌ Error en insert: {e}")
                

    async def insertar_documento_simple(
        self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int,
        ruta_s3: str, url_auto: str, origen: str, tipo_documento: str, fecha_registro_tyba:str
    ) -> bool:
        """
        Inserta un documento en CONTROL_AUTOS_RAMA_1 con las columnas básicas.
        """
        try:
            query = f"""
                INSERT INTO CONTROL_AUTOS_RAMA_1 (
                    FECHA_NOTIFICACION,
                    RADICACION,
                    CONSECUTIVO,
                    RUTA_S3,
                    URL_AUTO,
                    ORIGEN,
                    TIPO_DOCUMENTO,
                    FECHA_AUTO
                    
                ) VALUES (
                    TO_DATE(:fecha_notificacion, 'DD-MM-YYYY'),
                    :radicacion,
                    :consecutivo,
                    :ruta_s3,
                    :url_auto,
                    :origen,
                    :tipo_documento,
                    TO_DATE(:fecha_auto, 'DD-MM-YYYY-HH24:MI:SS')
                )
            """

            def _execute():
                with conn.cursor() as cursor:
                    cursor.execute(query, {
                        "fecha_notificacion": fecha_notificacion,
                        "radicacion": radicacion,
                        "consecutivo": consecutivo,
                        "ruta_s3": ruta_s3,
                        "url_auto": url_auto,
                        "origen": origen,
                        "tipo_documento": tipo_documento,
                        "fecha_auto":fecha_registro_tyba
                    })

            await asyncio.to_thread(_execute)
            await asyncio.to_thread(conn.commit)

            return True

        except Exception as error:
            logging.error(f"❌ Error en insertar_documento_simple: {error}")
            return False


    async def actualizar_hora(
        self,
        conn,
        fecha_notificacion: str,
        consecutivo: int,
        radicacion: str,
        fecha_registro_tyba: str
    ) -> bool:
        """
        Actualiza la columna RESUELVE en CONTROL_AUTOS_RAMA_1
        usando FECHA_NOTIFICACION, CONSECUTIVO y RADICACION como filtro.
        """
        try:
            query = """
                UPDATE CONTROL_AUTOS_RAMA_1
                SET FECHA_AUTO = TO_DATE(:fecha_auto, 'DD-MM-YYYY-HH24:MI:SS')
                WHERE FECHA_NOTIFICACION = TO_DATE(:fecha_notificacion, 'DD-MM-YYYY')
                AND CONSECUTIVO = :consecutivo
                AND RADICACION = :radicacion
            """

            def _execute():
                with conn.cursor() as cursor:
                    cursor.execute(query, {
                        "fecha_auto": fecha_registro_tyba,
                        "fecha_notificacion": fecha_notificacion,
                        "consecutivo": consecutivo,
                        "radicacion": radicacion
                    })

            await asyncio.to_thread(_execute)
            await asyncio.to_thread(conn.commit)

            return True

        except Exception as error:
            logging.error(f"❌ Error en actualizar_resuelve: {error}")
            return False