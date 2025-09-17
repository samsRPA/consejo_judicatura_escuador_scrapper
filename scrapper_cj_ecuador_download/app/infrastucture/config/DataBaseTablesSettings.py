from app.infrastucture.config.EnvConfig import EnvConfig
from pydantic import Field

class DataBaseTablesSettings(EnvConfig):
    DB_TABLE_NAME_CAR: str = Field(..., alias='DB_TABLE_NAME_CAR')
