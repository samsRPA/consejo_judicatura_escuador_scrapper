from abc import ABC, abstractmethod
from pathlib import Path

class IProcessDataService(ABC):
    
    @abstractmethod
    def procesar_actuaciones_judiciales(self,data,paths:Path,save_file):
        pass

    @abstractmethod
    def procesar_uuid_con_documentos(self,list):
        pass

    @abstractmethod 
    def procesar_consecutivos(self,data):
        pass
     
