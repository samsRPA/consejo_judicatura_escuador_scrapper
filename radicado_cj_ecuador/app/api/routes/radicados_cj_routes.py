from fastapi import status
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from app.dependencies.Dependencies import Dependencies
from app.domain.interfaces.IRadicadosCJService import IRadicadosCJService

#from app.application.dto.KeyResponseDto import KeyResponseDto
#from radicado_cj_ecuador.app.domain.interfaces.IRadicadosCJService import IkeysTybaService
#from app.application.dto.PublishKeysRequestDto import PublishKeysRequestDto

router = APIRouter()


@router.get("/radicadosCJ",  response_model_exclude_none=True,
            status_code=status.HTTP_202_ACCEPTED)
@inject
async def get_radicados(radicados_cj_service: IRadicadosCJService = Depends(Provide[Dependencies.radicados_cj_service])):
    try:
        raw_radicados = await radicados_cj_service.getAllRadicadosCJ()

        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=raw_radicados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post(
    "/radicadosCJ/queues",
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED
)
@inject
async def publishAllRadicados(
      
       radicados_cj_service:IRadicadosCJService = Depends(Provide[Dependencies.radicados_cj_service])
):
    try:
        raw_radicados = await radicados_cj_service.publishRadicadosCJ()

        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content="✔️ Mensajes enviados a la cola radicados_cj_ecuador ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

