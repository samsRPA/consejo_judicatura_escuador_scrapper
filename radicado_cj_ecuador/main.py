
from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

from app.api.views import getApiRouter
from app.dependencies.Dependencies import Dependencies

from app.infrastucture.config.Settings import load_config

# ============ Configuración de logging ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
)

logger= logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()

    dependency = Dependencies()
    dependency.settings.override(config)
    app.container = dependency
    db = dependency.data_base()
    producer = dependency.rabbitmq_producer()
    

    try:
        await producer.connect()
        await db.connect()

        yield

     
    except Exception as error:
        logger.exception("❌ Error durante la ejecución principal", exc_info=error)
    finally:
        try:
            await producer.close()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cerrar RabbitMQ correctamente: {e}")
        try:
            if db.is_connected:
                await db.close_connection()
        except Exception as error:
            logger.warning(f"⚠️ No se pudo cerrar la DB correctamente: {error}")


app = FastAPI(
    lifespan=lifespan,
    title="radicados actuaciones sujetos consejo judicatura ecuadosAPI Service",
    description=(
        "radicados consejo judicatura ecuador  app"
    ),
    version="0.1.0",
    contact={
        "name": "Rpa Litigando Department",
        "email": "correog@gmail.com",
    },
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/swagger",
    redoc_url="/api/v1/redocs",
)


app.include_router(getApiRouter())

@app.get("/")
def default():
    return {"mensaje": "Hello notificaciones tyba"}

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
