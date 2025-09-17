
from prometheus_client import Counter, Histogram
# ================== Métricas Prometheus ==================
radicados_requests_total = Counter(
    'radicados_requests_total', 'Total de solicitudes al endpoint radicadosCJ'
)
radicados_errors_total = Counter(
    'radicados_errors_total', 'Total de errores en el endpoint radicadosCJ'
)
radicados_response_time = Histogram(
    'radicados_response_time_seconds', 'Tiempo de respuesta del endpoint radicadosCJ'
)

radicados_service_requests_total = Counter(
    'radicados_service_requests_total',
    'Número total de solicitudes al servicio getAllRadicadosCJ'
)

radicados_service_errors_total = Counter(
    'radicados_service_errors_total',
    'Número total de errores al invocar el servicio getAllRadicadosCJ'
)

radicados_service_response_time = Histogram(
    'radicados_service_response_time_seconds',
    'Tiempo de respuesta del servicio getAllRadicadosCJ en segundos'
)