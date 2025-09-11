from abc import ABC, abstractmethod

class IDownloadService(ABC):

    @abstractmethod
    async def download_documents(self,fila,actuaciones_dir):
        pass
    
    @abstractmethod
    def upload_file_s3(self,ruta_pdf):
        pass

    @abstractmethod
    async def run_download(self):
        pass
    
    # @abstractmethod
    # def download_documents_simultaneously(actuaciones):
    #     pass