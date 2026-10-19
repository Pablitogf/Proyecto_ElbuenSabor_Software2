from datetime import datetime


class RelojDelSistema:
    """Hora local del servidor (el restaurante opera en un solo huso horario)."""

    def ahora(self) -> datetime:
        return datetime.now().replace(microsecond=0)
