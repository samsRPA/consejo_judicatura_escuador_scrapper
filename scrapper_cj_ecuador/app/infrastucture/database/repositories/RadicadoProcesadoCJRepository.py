import asyncio
import logging


class RadicadoProcesadoCJRepository:
    
    
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
        
    async def radicacion_procesada(self, conn, radicacion: str) -> bool:
        """
        Verifica si ya existe un radicado en CONTROL_AUTOS_RAMA_1.
        Retorna True si hay filas (✅ procesado), False en caso contrario.
        """
        try:
            query = """
                SELECT 1
                FROM CONTROL_AUTOS_RAMA_1
                WHERE RADICACION = :radicacion
                FETCH FIRST 1 ROWS ONLY
            """

            async def _execute():
                async with conn.cursor() as cursor:
                    await cursor.execute(query, {"radicacion": radicacion})
                    rows= await cursor.fetchone()
                    return rows

            result = await _execute()

            if result:
                self.logger.info(f"✅ Radicado {radicacion} ya procesado")
                return True
            else:
                self.logger.info(f"🔎 radicado {radicacion} no se procesado, se recorrera completamente.")
                return False

        except Exception as error:
            self.logger.error(f"❌ Error en radicacion_procesada: {error}")
            raise
