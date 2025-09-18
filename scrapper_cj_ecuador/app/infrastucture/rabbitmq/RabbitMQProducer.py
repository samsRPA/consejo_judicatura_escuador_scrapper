import json
import logging
import asyncio
import aio_pika

from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer


class RabbitMQProducer(IRabbitMQProducer):
    logger = logging.getLogger(__name__)

    def __init__(self, host, port, pub_queue_name, user, password):
        self.host = host
        self.port = port
        self.pub_queue_name = pub_queue_name
        self.user = user
        self.password = password
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
                heartbeat=300,       # ❤️ mismo que el servidor
                timeout=30,          # ⏳ más margen
                retry_interval=30    # 🔁 reintento cada 30s
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.pub_queue_name, durable=True)
            self.logger.info("✅ Conectado a RabbitMQ - Producer")
        except Exception as error:
            self.logger.error(f"❌ Error conectando al Producer: {error}")
            raise error

    async def publishMessage(self, message):
        try:
            if not self.connection or self.connection.is_closed:
                self.logger.warning("⚠️ Conexión cerrada, reconectando Producer...")
                await self.connect()

            if not self.channel or self.channel.is_closed:
                self.logger.warning("⚠️ Canal cerrado, reabriendo...")
                self.channel = await self.connection.channel()

            body = json.dumps(message).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # ✅ persistencia
                ),
                routing_key=self.pub_queue_name,
            )
            self.logger.info(f"📤 Mensaje enviado a {self.pub_queue_name}")

        except (aio_pika.exceptions.ChannelInvalidStateError, asyncio.CancelledError) as error:
            self.logger.error(f"❌ Error de estado en publishMessage: {error}, reintentando...")
            await asyncio.sleep(2)
            return await self.publishMessage(message)  # 🔁 reintento
        except Exception as error:
            self.logger.error(f"❌ Error enviando mensaje {error}")
            raise error

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()
            self.logger.info("🔌 Conexión con RabbitMQ cerrada")
