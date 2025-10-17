from dependency_injector import containers, providers

#from radicado_cj_ecuador.app.application.services.RadicadosCJService import KeysTybaService
from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
from app.domain.interfaces.IRadicadosCJService import IRadicadosCJService
from app.infrastucture.config.Settings import Settings
from app.infrastucture.database.OracleDB import OracleDB
from app.infrastucture.rabbitmq.RabbitMQProducer import RabbitMQProducer
from app.application.services.RadicadosCJService import RadicadosCJService
from app.infrastucture.database.repositories.RadicadosCJRepository import RadicadosCJRepository


class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)
    wiring_config = containers.WiringConfiguration(
        modules=["app.api.routes.radicados_cj_routes"]
    )
    # Provider de db
    data_base: providers.Singleton[IDataBase] = providers.Singleton(
        OracleDB,
        db_user=settings.provided.data_base.DB_USER,
        db_password=settings.provided.data_base.DB_PASSWORD,
        db_host=settings.provided.data_base.DB_HOST,
        db_port=settings.provided.data_base.DB_PORT,
        db_service_name=settings.provided.data_base.DB_SERVICE_NAME,
    )

    radicados_cj_repository = providers.Factory(
        RadicadosCJRepository,
        )

    # Provider del productor, expuesto como su interfaz (desacoplado)
    rabbitmq_producer: providers.Singleton[IRabbitMQProducer] = providers.Singleton(
        RabbitMQProducer,
        host=settings.provided.rabbitmq.HOST,
        port=settings.provided.rabbitmq.PORT,
        pub_queue_name=settings.provided.rabbitmq.PUB_QUEUE_NAME,
        user=settings.provided.rabbitmq.RABBITMQ_USER,
        password=settings.provided.rabbitmq.RABBITMQ_PASS

    )

    radicados_cj_service: providers.Factory[IRadicadosCJService] = providers.Factory(
        RadicadosCJService,
        producer=rabbitmq_producer,
        db=data_base,
        repository=radicados_cj_repository,
    )
