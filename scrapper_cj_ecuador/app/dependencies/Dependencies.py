from dependency_injector import containers, providers
from app.application.services.scrapper.ScrapperService import ScrapperService
from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.domain.interfaces.IScrapperService import IScrapperService
from app.infrastucture.config.Settings import Settings
from app.infrastucture.rabbitmq.RabbitMQConsumer import RabbitMQConsumer
from app.domain.interfaces.IProcessDataService import IProcessDataService
from app.application.services.scrapper.ProcessDataService import ProcessDataService
from app.application.services.scrapper.GetDataService import GetDataService
from app.domain.interfaces.IGetDataService import IGetDataService
from app.infrastucture.rabbitmq.RabbitMQProducer import RabbitMQProducer
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
from app.application.services.scrapper.ActuacionesPublishService import ActuacionesPublishService
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService



class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)


    get_data_service: providers.Factory[IGetDataService] = providers.Factory(
        GetDataService,
    )
    
    process_data_service: providers.Factory[IProcessDataService] = providers.Factory(
        ProcessDataService,
       
    )

     # Provider del productor, expuesto como su interfaz (desacoplado)
    rabbitmq_producer: providers.Singleton[IRabbitMQProducer] = providers.Singleton(
        RabbitMQProducer,
        host=settings.provided.rabbitmq.HOST,
        port=settings.provided.rabbitmq.PORT,
        pub_queue_name=settings.provided.rabbitmq.PUB_QUEUE_NAME_DOCUMENTS,
        user=settings.provided.rabbitmq.RABBITMQ_USER,
        password=settings.provided.rabbitmq.RABBITMQ_PASS

    )

    actuaciones_publish_service:providers.Factory[IActuacionesPublishService] = providers.Factory(
        ActuacionesPublishService,
        producer=rabbitmq_producer
    )

    scrapper_service: providers.Factory[IScrapperService] = providers.Factory(
        ScrapperService,
        get_data_service,
        process_data_service,
        actuaciones_publish_service
    )




   
    # Provider del consumidor
    rabbitmq_consumer: providers.Singleton[IRabbitMQConsumer] = providers.Singleton(
        RabbitMQConsumer,
        host=settings.provided.rabbitmq.HOST,
        port=settings.provided.rabbitmq.PORT,
        pub_queue_name=settings.provided.rabbitmq.PUB_QUEUE_NAME,
        prefetch_count=settings.provided.rabbitmq.PREFETCH_COUNT,
        user=settings.provided.rabbitmq.RABBITMQ_USER,
        password=settings.provided.rabbitmq.RABBITMQ_PASS,
        scrapper_service=scrapper_service.provider
    )
