import logging
import contextvars

logger = logging.getLogger(__name__)

_tabla_auditoria: str | None = None
_trazar_lecturas: bool = False
_auditando: contextvars.ContextVar[bool] = contextvars.ContextVar('_auditando', default=False)

def configurar_auditoria(tabla: str = 'EventoAuditoria', *, trazar_lecturas: bool = False) -> None:
    """Activa el registro de auditoría de operaciones SQL.

    Debe llamarse una vez al iniciar la aplicación. A partir de ese momento,
    toda instrucción INSERT, UPDATE o DELETE ejecutada a través del ORM queda
    registrada en la tabla indicada. Si no se llama, no se registra nada.

    trazar_lecturas: si True, también registra instrucciones SELECT.
    Por defecto False — en sistemas con muchas lecturas el volumen puede ser alto.
    """
    global _tabla_auditoria, _trazar_lecturas
    _tabla_auditoria = tabla
    _trazar_lecturas = trazar_lecturas
