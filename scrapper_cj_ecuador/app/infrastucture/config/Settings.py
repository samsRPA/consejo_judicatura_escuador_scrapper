from pydantic_settings import BaseSettings


from app.infrastucture.config.RabbitMQSettings import RabbitMQSettings



class Settings(BaseSettings):
    rabbitmq : RabbitMQSettings = RabbitMQSettings()



def load_config() -> Settings:
    return Settings()
