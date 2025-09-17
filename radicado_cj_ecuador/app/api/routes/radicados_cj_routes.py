from fastapi import status
from fastapi.responses import JSONResponse, Response
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from app.dependencies.Dependencies import Dependencies
from app.domain.interfaces.IRadicadosCJService import IRadicadosCJService
import time

#from app.application.dto.KeyResponseDto import KeyResponseDto
#from radicado_cj_ecuador.app.domain.interfaces.IRadicadosCJService import IkeysTybaService
#from app.application.dto.PublishKeysRequestDto import PublishKeysRequestDto

router = APIRouter()

from app.application.dto.MetricsDto import(
    radicados_requests_total,
    radicados_errors_total,
    radicados_response_time
    )
@router.get("/radicadosCJ",  response_model_exclude_none=True,
            status_code=status.HTTP_202_ACCEPTED)
@inject
async def get_radicados(radicados_cj_service: IRadicadosCJService = Depends(Provide[Dependencies.radicados_cj_service])):
    start_time = time.time()
    radicados_requests_total.inc()
    try:
         # Contador de solicitudes
        raw_radicados = await radicados_cj_service.getAllRadicadosCJ()

        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=raw_radicados)
    except Exception as e:
        radicados_errors_total.inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        radicados_response_time.observe(time.time() - start_time)



@router.post(
    "/radicadosCJ/queues",
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED
)
@inject
async def publishAllRadicados(
      
       radicados_cj_service:IRadicadosCJService = Depends(Provide[Dependencies.radicados_cj_service])
):
    start_time = time.time()
    radicados_requests_total.inc()
    try:
        
        await radicados_cj_service.publishRadicadosCJ()

        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content="✔️ Mensajes enviados a la cola radicados_cj_ecuador ")
    except Exception as e:
        radicados_errors_total.inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        radicados_response_time.observe(time.time() - start_time)

