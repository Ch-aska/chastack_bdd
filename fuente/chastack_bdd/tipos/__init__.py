from typing import Protocol, runtime_checkable, Self, TypeAlias, Optional, Any, AnyStr, Unpack,Union,Dict,List, get_origin, Collection, TypeVar, Generic
from decimal import Decimal
from datetime import datetime,date,time,timedelta,timezone
from re import Match

from chastack_bdd.tipos.enum_sql import *
from chastack_bdd.tipos.unico_sql import *
from solteron import Solteron
### BDD
Resultado : TypeAlias = dict[str,Any]

class TipoCondicion(EnumSQL):
    IGUAL = '='
    PARECIDO = 'LIKE'
    DIFERENTE = '!='
    MAYOR = '>'
    MENOR = '<'
    MAYOR_O_IGUAL = '>='
    MENOR_O_IGUAL = '<='
    ES = 'IS'
    NO_ES = 'IS NOT'
    EN = 'IN'

class TipoUnion(EnumSQL):
    INNER = 1
    OUTER = 2
    LEFT  = 3
    RIGHT = 4
    FULL  = 5

class TipoOrden(EnumSQL):
    ASC = 1
    DESC  = 2

class ArgumentoURL(EnumSQL):
    ORDENAR_POR = "ordenarPor"
    TIPO_ORDEN = "tipoOrden"
    BUSCAR = "buscar"
    ID = "idx"
    NUMERO_PAGINA = "pag"

