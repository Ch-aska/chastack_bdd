from json import dumps,loads
from chastack_bdd.tipos import *
from solteron import Solteron
from sobrecargar import sobrecargar
from secrets import token_urlsafe
from re import findall,match,sub
from typing import get_type_hints, get_origin, get_args


def tipoSQLDesdePython(tipo_python: type) -> str:
    """
    Devuelve el tipo SQL correspondiente a un tipo de Python.
    Si el tipo es un Enum generado por __resolverTipo, intenta reconstruir el ENUM SQL.
    
    Parámetros:
        :arg tipo_python type: el tipo de Python (p. ej., int, str, Enum, etc.)

    Devuelve:
        :arg str: el tipo SQL correspondiente
    """
    tipos: dict[type, str] = {
        int: 'int',
        float: 'double',
        Decimal: 'decimal(10,2)',
        datetime: 'datetime',
        date: 'date',
        time: 'time',
        str: 'varchar(255)',
        bool: 'tinyint(1)',
        bytes: 'varbinary(255)',
        bytearray: 'blob',
        dict: 'json',
    }

    # Enums definidos dinámicamente por Tabla.__resolverTipo
    if isinstance(tipo_python, type) and issubclass(tipo_python, EnumSQL):
        valores = [f"'{e.name}'" for e in tipo_python if e.name != '_invalido']
        return f"enum({','.join(valores)})"

    

    return tipos.get(tipo_python, 'text')

class ExprSQL(str):
    """Expresión SQL cruda que se interpola sin escapar ni entrecomillar."""
    pass


def _escaparParaMySQL(texto: str) -> str:
    """Escapa caracteres especiales para SQL concatenado en MySQL.

    MySQL interpreta backslashes como escape characters por defecto
    (a menos que esté activado NO_BACKSLASH_ESCAPES). Esta función
    escapa los caracteres que rompen queries SQL construidas por
    concatenación de strings.

    IMPORTANTE: El orden de los replacements es crítico.
    Backslash DEBE ser el primero para evitar doble-escape.

    Parámetros:
        :arg texto str: El texto a escapar.

    Devuelve:
        :return str: El texto con caracteres especiales escapados.
    """
    texto = texto.replace('\\', '\\\\')   # \ → \\ (PRIMERO, antes de cualquier otro!)
    texto = texto.replace("'", "''")       # ' → '' (escape SQL estándar)
    texto = texto.replace('\n', '\\n')     # newline → literal \n
    texto = texto.replace('\r', '\\r')     # carriage return → literal \r
    texto = texto.replace('\0', '')        # null byte → eliminar (corta strings en MySQL)
    texto = texto.replace('\t', '\\t')     # tab → literal \t
    return texto

def formatearValorParaSQL(valor: Any, html : bool = False, parecido : bool = False) -> str:
    """
    Formatea un valor de Python a una representación adecuada para SQL.
    """
    prefijo = sufijo = "%" if parecido else ""
    infijo = "%" if parecido else " "
    if isinstance(valor, ExprSQL):
        return str(valor)
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, (list, tuple)):
        return f"'[{','.join(f"\"{str(v)}\"" for v in valor)}]'"
    if isinstance(valor, Decimal):
        return str(valor.to_eng_string())
    if isinstance(valor, (date, datetime, time)):
        return f"'{valor.isoformat()}'"
    if isinstance(valor, dict):
        return f"'{_escaparParaMySQL(dumps(valor))}'"
    if isinstance(valor, bytes):
        return f"X'{valor.hex()}'"
    if isinstance(valor, Enum):
        return str(valor.value) if isinstance(valor.value, int) else f"'{valor.name}'"
    if isinstance(valor, str):
        return f"'{prefijo}{_escaparParaMySQL(valor).replace(" ", infijo)}{sufijo}'"

    return f"'{prefijo}{_escaparParaMySQL(str(valor)).replace(" ", infijo)}{sufijo}'"

def esSubclaseUnion(cls: type, clase_objetivo: Union[type, tuple[Union[type, tuple[Any, ...]], ...]], /) -> bool:
    """Devuelve True si cls es (o contiene) una subclase de objetivo"""
    origen = get_origin(cls)
    argumentos = get_args(cls)

    if origen is Union:
        return any(
            isinstance(arg, type) and issubclass(arg, clase_objetivo)
            for arg in argumentos if arg is not type(None)
        )
    return isinstance(cls, type) and issubclass(cls, clase_objetivo)

def desenvolverTipo(tipo : Union[type, Any]):
    if isinstance(tipo, type):
        return tipo
    
    origen = get_origin(tipo)
    argumentos = get_args(tipo)
    #print("\n###########################2\n",tipo, origen, argumentos,"\n###########################\n")
    if origen is Union:
        for arg in argumentos:
            if isinstance(arg,type):
                return arg

def atributoPublico(nombre_atributo: str) -> str:
    return f"{sub("_.*__","",nombre_atributo)}".replace("__","",1)

def atributoPrivado(obj: Any, nombre_atributo: str) -> str:
    return f"_{obj.__class__.__name__}__{atributoPublico(nombre_atributo)}"

def tieneAtributoPrivado(obj: Any, nombre_atributo: str) -> bool:
    return hasattr(obj,atributoPrivado(obj,nombre_atributo))

def tieneAtributo(obj: Any, nombre_atributo: str) -> bool:
    return hasattr(obj,nombre_atributo) or tieneAtributoPrivado(obj,nombre_atributo)

def devolverAtributoPrivado(obj: Any, nombre_atributo: str, por_defecto = None) -> Any:
    return getattr(obj,atributoPrivado(obj,nombre_atributo), por_defecto)

def asignarAtributoPrivado(obj: Any, nombre_atributo: str, valor) -> None:
    setattr(obj,atributoPrivado(obj,nombre_atributo), valor)

def devolverAtributo(obj: Any, nombre_atributo: str, por_defecto = None) -> Any:
    return getattr(obj,atributoPrivado(obj,nombre_atributo) if '__' in nombre_atributo else nombre_atributo, por_defecto)