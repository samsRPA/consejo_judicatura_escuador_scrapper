from pydantic_settings import BaseSettings

from app.infrastucture.config.DataBaseSettings import DataBaseSettings
#from app.infrastucture.config.DataBaseTablesSettings import DataBaseTablesSettings
from app.infrastucture.config.RabbitMQSettings import RabbitMQSettings

class Settings(BaseSettings):
    data_base: DataBaseSettings = DataBaseSettings()
    #data_base_tables: DataBaseTablesSettings = DataBaseTablesSettings()
    rabbitmq : RabbitMQSettings = RabbitMQSettings()

def load_config() -> Settings:
    return Settings()
