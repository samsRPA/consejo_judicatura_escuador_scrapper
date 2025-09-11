from fastapi import APIRouter

from app.api.routes import radicados_cj_routes

apiRouter = APIRouter(prefix="/api/v1")
apiRouter.include_router(radicados_cj_routes.router, tags=["radicados_cj"])

def getApiRouter():
    return apiRouter