from dependency_injector import containers, providers
from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.infrastucture.config.Settings import Settings
from app.infrastucture.rabbitmq.RabbitMQConsumer import RabbitMQConsumer
from app.infrastucture.AWS.S3Manager import S3Manager
from app.domain.interfaces.IS3Manager import IS3Manager
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.OracleDB import OracleDB
from app.infrastucture.database.repositories.RadicadosCJRepository import RadicadosCJRepository
from app.domain.interfaces.IDownloadService import IDownloadService
from app.application.services.scrapper.DownloadService import DownloadService



class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)

# Provider de db
    data_base: providers.Singleton[IDataBase] = providers.Singleton(
        OracleDB,
        db_user=settings.provided.data_base.DB_USER,
        db_password=settings.provided.data_base.DB_PASSWORD,
        db_host=settings.provided.data_base.DB_HOST,
        db_port=settings.provided.data_base.DB_PORT,
        db_service_name=settings.provided.data_base.DB_SERVICE_NAME,
    )

      # Provider de Repositories
    radicados_CJ_repository = providers.Factory(
        RadicadosCJRepository,
        table_car=settings.provided.data_base_tables.DB_TABLE_NAME_CAR,
       
    )


     
    S3_manager_litigando: providers.Singleton[IS3Manager] = providers.Singleton(
        S3Manager,
        awsAccessKey = settings.provided.s3.awsAccessKey,
        awsSecretKey = settings.provided.s3.awsSecretKey,
        bucketName = settings.provided.s3.bucketLitigando,
        s3Prefix = settings.provided.s3.prefixLitigando,
    )



    download_service: providers.Factory[IDownloadService] = providers.Factory(
        DownloadService,
        data_base,
        radicados_CJ_repository,
        S3_manager_litigando
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
        download_service=download_service
    )
