from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.dominio.excepciones import (
    ErrorDeDominio,
    RecursoNoEncontradoError,
    ReglaDeNegocioError,
)

CODIGO_HTTP_POR_TIPO_DE_ERROR: dict[type[ErrorDeDominio], int] = {
    RecursoNoEncontradoError: status.HTTP_404_NOT_FOUND,
    ReglaDeNegocioError: status.HTTP_409_CONFLICT,
}


def registrar_manejadores_de_error(aplicacion: FastAPI) -> None:
    aplicacion.add_exception_handler(ErrorDeDominio, _responder_error_de_dominio)


async def _responder_error_de_dominio(_: Request, error: ErrorDeDominio) -> JSONResponse:
    return JSONResponse(status_code=_codigo_http_para(error), content={"detalle": str(error)})


def _codigo_http_para(error: ErrorDeDominio) -> int:
    for tipo_de_error, codigo in CODIGO_HTTP_POR_TIPO_DE_ERROR.items():
        if isinstance(error, tipo_de_error):
            return codigo
    return status.HTTP_400_BAD_REQUEST
