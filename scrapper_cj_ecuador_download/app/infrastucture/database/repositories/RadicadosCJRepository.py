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

    async def insertar_documento_simple(
        self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int,
        ruta_s3: str, url_auto: str, origen: str, tipo_documento: str
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
                    TIPO_DOCUMENTO
                ) VALUES (
                    TO_DATE(:fecha_notificacion, 'DD-MM-YYYY'),
                    :radicacion,
                    :consecutivo,
                    :ruta_s3,
                    :url_auto,
                    :origen,
                    :tipo_documento
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
                        "tipo_documento": tipo_documento
                    })

            await asyncio.to_thread(_execute)
            await asyncio.to_thread(conn.commit)

            return True

        except Exception as error:
            logging.error(f"❌ Error en insertar_documento_simple: {error}")
            return False
