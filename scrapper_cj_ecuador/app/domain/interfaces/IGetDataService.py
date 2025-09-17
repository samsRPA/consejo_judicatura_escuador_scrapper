from abc import ABC, abstractmethod
from pathlib import Path

class IGetDataService(ABC):
    
    @abstractmethod
    def get_incidente_judicatura(self,radicado: str,json_dir:Path):
          pass

    @abstractmethod
    def get_actuaciones_judiciales(self,idMovimientoJuicioIncidente, radicado, id_judicatura, idIncidenteJudicatura, nombreJudicatura, incidente):
        pass

    @abstractmethod
    def get_anexos(actuacion_procesada):
        pass

