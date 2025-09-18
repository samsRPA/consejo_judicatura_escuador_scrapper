import asyncio
import aio_pika
import logging
from typing import Callable

from app.application.dto.ScrapperRequest import ScrapperRequest
from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.domain.interfaces.IScrapperService import IScrapperService


class RabbitMQConsumer(IRabbitMQConsumer):
    logger = logging.getLogger(__name__)

    def __init__(self, host: str, port: int, pub_queue_name: str, prefetch_count: int,
                 scrapper_service: Callable[[str], IScrapperService], user, password):
        self.host = host
        self.port = port
        self.pub_queue_name = pub_queue_name
        self.prefetch_count = prefetch_count
        self.scrapper_service = scrapper_service
        self.user = user
        self.password = password

        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.queue: aio_pika.abc.AbstractQueue | None = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
                heartbeat=300,
                timeout=30,
                retry_interval=30
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            self.queue = await self.channel.declare_queue(
                self.pub_queue_name,
                durable=True
            )

            self.logger.info("✅ Conectado a RabbitMQ - Consumer")

        except Exception as error:
            self.logger.error(f"❌ Error conectando al consumer: {error}")
            raise error

    async def callback(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process(ignore_processed=True):
                raw_body = message.body.decode()
                request = ScrapperRequest.fromRaw(raw_body)

                service = self.scrapper_service(request)
                await service.runScrapper()

        except asyncio.CancelledError:
            self.logger.warning("⚠️ Tarea cancelada mientras procesaba mensaje, reencolando...")
            await message.nack(requeue=True)
            raise
        except aio_pika.exceptions.ChannelInvalidStateError:
            self.logger.error("❌ Canal inválido al procesar mensaje. Reencolando...")
            await message.nack(requeue=True)
        except Exception as e:
            self.logger.error(f"❌ Error procesando mensaje: {e}")
            try:
                await message.nack(requeue=False)
            except aio_pika.exceptions.MessageProcessError:
                self.logger.warning("⚠️ Intento de NACK en un mensaje ya procesado.")

    async def startConsuming(self):
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    self.logger.info("📡 Conexión no establecida o cerrada. Conectando...")
                    await self.connect()

                if self.queue:
                    consumer_tag = await self.queue.consume(self.callback, no_ack=False)
                    self.logger.info(f"🎧 Esperando mensajes en {self.pub_queue_name}...")

                    while not self.connection.is_closed:
                        await asyncio.sleep(5)

                    await self.queue.cancel(consumer_tag)

            except asyncio.CancelledError:
                self.logger.info("👋 Interrupción manual detectada en consumer.")
                break
            except Exception as e:
                self.logger.error(f"⚠️ Error en loop de consumo: {e}. Reintentando en 5s...")
                await asyncio.sleep(5)

        if self.connection:
            await self.connection.close()
            self.logger.info("🔌 Conexión a RabbitMQ cerrada.")
