from app.application.dto.ScrapperRequest import ScrapperRequest
from app.domain.interfaces.IScrapperService import IScrapperService
from app.domain.interfaces.IGetDataService import IGetDataService
from app.domain.interfaces.IProcessDataService import IProcessDataService
import logging
from app.application.dto.HoyPathsDto import HoyPathsDto
from app.domain.interfaces.IActuacionesPublishService import IActuacionesPublishService

from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.RadicadoProcesadoCJRepository import RadicadoProcesadoCJRepository
from app.domain.interfaces.ICJEcuadorScrapper import ICJEcuadorScrapper

class ScrapperService(IScrapperService):


  
    def __init__(self,body: ScrapperRequest,cj_ecuador_scrapper:ICJEcuadorScrapper, ):
        self.body = body
        self.cj_ecuador_scrapper=cj_ecuador_scrapper
        self.logger= logging.getLogger(__name__)

    async def runScrapper(self):
        
        try:
            # Construir el DTO que espera run_multi
            radicado= ScrapperRequest(
                radicado=self.body.radicado,
            )
            
            await self.cj_ecuador_scrapper.scrapper(radicado.radicado)

        except Exception as e:
            self.logger.error(f"❌ Error : {e}")
            raise e
       
