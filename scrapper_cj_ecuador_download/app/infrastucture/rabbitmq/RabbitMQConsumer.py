import asyncio
import aio_pika
import logging
from typing import Callable

from app.application.dto.AutosRequestDto import AutosRequestDto
from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.domain.interfaces.IDownloadService import IDownloadService



class RabbitMQConsumer(IRabbitMQConsumer):

    def __init__(self, host: str, port: int, pub_queue_name: str, prefetch_count: int,
                 download_service: Callable[[str], IDownloadService], user, password):
        self.host = host
        self.port = port
        self.pub_queue_name = pub_queue_name
        self.prefetch_count = prefetch_count
        self.download_service = download_service
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
                timeout=10,
                heartbeat=300,      # ❤️ heartbeat cada 5 minutos
                retry_interval=5,
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            self.queue = await self.channel.declare_queue(
                self.pub_queue_name,
                durable=True
            )

            logging.info("✅ Conectado a RabbitMQ - Consumer")

        except Exception as error:
            logging.error(f"❌ Error conectando al consumer: {error}")
            raise error

    async def callback(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process(ignore_processed=True):
                raw_body = message.body.decode()
                request = AutosRequestDto.fromRaw(raw_body)

                # Crear servicio y correr scrapper
                service: IDownloadService = self.download_service
                await service.run_download(request)

        except aio_pika.exceptions.ChannelInvalidStateError:
            logging.error("❌ Canal inválido al procesar mensaje. Reencolando...")
            try:
                await message.nack(requeue=True)
            except Exception:
                logging.warning("⚠️ No se pudo hacer NACK, canal ya cerrado.")
        except Exception as e:
            logging.error(f"❌ Error procesando mensaje: {e}")
            try:
                await message.nack(requeue=False)
            except aio_pika.exceptions.MessageProcessError:
                logging.warning("⚠️ Intento de NACK en un mensaje ya procesado.")

    async def startConsuming(self):
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    logging.info("📡 Conexión no establecida o cerrada. Conectando...")
                    await self.connect()

                if self.queue:
                    await self.queue.consume(self.callback, no_ack=False)
                    logging.info("🎧 Esperando mensajes...")

                while not self.connection.is_closed:
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                logging.info("👋 Interrupción manual detectada.")
                break
            except Exception as e:
                logging.error(f"⚠️ Error en loop de consumo: {e}. Reintentando en 5s...")
                await asyncio.sleep(5)

        # cierre limpio
        if self.connection:
            await self.connection.close()
            logging.info("🔌 Conexión a RabbitMQ cerrada.")
