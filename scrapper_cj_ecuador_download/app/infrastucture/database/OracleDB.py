import logging
import oracledb
import asyncio
from app.domain.interfaces.IDataBase import IDataBase

class OracleDB(IDataBase):
    def __init__(self, db_user: str, db_password: str, db_host: str, db_port: int, db_service_name: str):
        self._db_user = db_user
        self._password = db_password
        self._host = db_host
        self._port = db_port
        self._service_name = db_service_name
        self._pool = None


    @property
    def is_connected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        try:
            dsn = oracledb.makedsn(self._host, self._port, service_name=self._service_name)
            self._pool =  await asyncio.to_thread(
                oracledb.create_pool,
                user=self._db_user,
                password=self._password,
                dsn=dsn,
                min=1,
                max=5,
                increment=1
            )
            logging.info("✅ Pool de Oracle creado exitosamente.")
        except Exception as error:
            raise error

    async def acquire_connection(self):
        if not self._pool:
            raise Exception("Pool no inicializado, llama a connect primero")
        conn = await asyncio.to_thread(self._pool.acquire)
        return conn

    async def release_connection(self, conn):
        try:
            await asyncio.to_thread(conn.execute, "ROLLBACK")
        except Exception:
            pass
        await asyncio.to_thread(self._pool.release, conn)

    async def commit(self, conn):
        await asyncio.to_thread(conn.execute, "COMMIT")

    async def close_connection(self):
        if self._pool:
            await asyncio.to_thread(self._pool.close)
            self._pool = None
            logging.info("🔌 Conexión a Oracle cerrada correctamente.")