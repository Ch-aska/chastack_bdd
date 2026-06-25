import logging

logger = logging.getLogger(__name__)

_tabla_auditoria: str | None = None

def configurar_auditoria(tabla: str = 'EventoAuditoria') -> None:
    """Activa el registro de auditoría de mutaciones SQL.

    Debe llamarse una vez al iniciar la aplicación. A partir de ese momento,
    toda instrucción INSERT, UPDATE o DELETE ejecutada a través del ORM queda
    registrada en la tabla indicada. Si no se llama, no se registra nada.
    """
    global _tabla_auditoria
    _tabla_auditoria = tabla
