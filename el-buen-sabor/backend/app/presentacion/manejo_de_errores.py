"""Traduce errores de dominio a respuestas HTTP, en un solo lugar."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.dominio.excepciones import (
    AccesoDenegadoError,
    AutenticacionError,
    DatoInvalidoError,
    ErrorDeDominio,
    RecursoNoEncontradoError,
    ReglaDeNegocioError,
    ServicioExternoError,
)

CODIGO_HTTP_POR_FAMILIA: dict[type[ErrorDeDominio], int] = {
    RecursoNoEncontradoError: status.HTTP_404_NOT_FOUND,
    DatoInvalidoError: 422,
    ReglaDeNegocioError: status.HTTP_409_CONFLICT,
    AccesoDenegadoError: status.HTTP_403_FORBIDDEN,
    AutenticacionError: status.HTTP_401_UNAUTHORIZED,
    ServicioExternoError: status.HTTP_502_BAD_GATEWAY,
}


def registrar_manejadores_de_error(aplicacion: FastAPI) -> None:
    aplicacion.add_exception_handler(ErrorDeDominio, _responder_error_de_dominio)
    aplicacion.add_exception_handler(RequestValidationError, _responder_validacion)


async def _responder_error_de_dominio(_: Request, error: ErrorDeDominio) -> JSONResponse:
    cuerpo: dict = {"detalle": str(error), "tipo": type(error).__name__}
    if motivos := getattr(error, "motivos", None):
        cuerpo["motivos"] = motivos
    return JSONResponse(status_code=_codigo_http_para(error), content=cuerpo)


async def _responder_validacion(_: Request, error: RequestValidationError) -> JSONResponse:
    campos = ", ".join(str(e["loc"][-1]) for e in error.errors())
    return JSONResponse(
        status_code=422,
        content={"detalle": f"Revisa estos datos: {campos}.", "tipo": "DatosMalFormados"},
    )


def _codigo_http_para(error: ErrorDeDominio) -> int:
    for familia, codigo in CODIGO_HTTP_POR_FAMILIA.items():
        if isinstance(error, familia):
            return codigo
    return status.HTTP_400_BAD_REQUEST
