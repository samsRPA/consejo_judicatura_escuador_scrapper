from pydantic_settings import BaseSettings


from app.infrastucture.config.RabbitMQSettings import RabbitMQSettings
from app.infrastucture.config.S3ManagerSettings import S3ManagerSettings
from app.infrastucture.config.DataBaseSettings import DataBaseSettings
from app.infrastucture.config.DataBaseTablesSettings import DataBaseTablesSettings
class Settings(BaseSettings):
    s3 : S3ManagerSettings = S3ManagerSettings()
    data_base: DataBaseSettings = DataBaseSettings()
    rabbitmq : RabbitMQSettings = RabbitMQSettings()
    data_base_tables: DataBaseTablesSettings = DataBaseTablesSettings()

def load_config() -> Settings:
    return Settings()
