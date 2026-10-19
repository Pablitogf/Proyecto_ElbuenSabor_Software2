"""Inicio de sesión y resolución del usuario de cada petición (RF-01, RNF-04)."""

from app.aplicacion.puertos import ServicioDeCredenciales, UnidadDeTrabajo
from app.dominio.excepciones import CredencialesInvalidasError, SesionInvalidaError
from app.dominio.usuario import Usuario


class GestorSesion:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, credenciales: ServicioDeCredenciales) -> None:
        self._uow = unidad_de_trabajo
        self._credenciales = credenciales

    def iniciar(self, nombre_usuario: str, pin: str) -> tuple[str, Usuario]:
        with self._uow:
            usuario = self._uow.usuarios.por_nombre_usuario(nombre_usuario.strip().lower())
        # Mismo mensaje si no existe o si el PIN falla: no revela qué usuarios hay.
        if usuario is None or not self._credenciales.verificar_pin(pin, usuario.hash_pin):
            raise CredencialesInvalidasError()
        return self._credenciales.emitir_token(usuario), usuario

    def usuario_de(self, token: str | None) -> Usuario:
        usuario_id = self._credenciales.leer_token(token) if token else None
        if usuario_id is None:
            raise SesionInvalidaError()
        with self._uow:
            usuario = self._uow.usuarios.obtener(usuario_id)
        if usuario is None:
            raise SesionInvalidaError()
        return usuario

    def usuarios(self) -> list[Usuario]:
        with self._uow:
            return self._uow.usuarios.listar()
