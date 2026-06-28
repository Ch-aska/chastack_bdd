from chastack_bdd.tipos import *
from chastack_bdd.errores import *
from chastack_bdd.utiles import *
from mysql.connector import connect
import logging

logger = logging.getLogger(__name__)

@runtime_checkable
class ProtocoloBaseDeDatos(Protocol):
    def DESCRIBE(self: Self, tabla :str) -> Self: ...
    def SELECT(self : Self, tabla : str, columnas : list[str], columnasSecundarias: Optional[dict[str, list[str]] ] = {}) -> Self:...
    def DELETE(self : Self, tabla : str) -> Self: ...
    def INSERT(self : Self, tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self: ...
    def UPDATE(self : Self, tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self: ...
    def WHERE(self : Self, tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]) -> Self: ...
    def JOIN(self : Self,   tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER) -> Self: ...
    def ORDER_BY(self, orden : [dict[str, TipoOrden]]): ...
    def LIMIT(self : Self, desplazamiento: int  , limite : int) -> Self: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type,excl_val,exc_tb) -> None: ...
    def ejecutar(self: Self) -> Self :...
    def devolverUnResultado(self: Self) -> Resultado :...
    def devolverResultados(self: Self) -> tuple[Resultado] :...
    def devolverIdUltimaInsercion(self:Self) -> Optional[int] :...

class InstruccionPrincipal():
    ''' 
        Clase que permite definir la clausula principal de una consulta SQL. 
        Altamente acoplada con la clase Consulta y dependiente de la misma.    
    '''

    __slots__ = \
    (
        '__instruccion'
    )
    def __init__(self):
        self.__instruccion = ''
    
    def chequearOcupado(self):
        if self.__instruccion: raise ErrorMalaSintaxisSQL("La clausula principal ya ha sido definida.")
    def esDescribe(self):
        self.__instruccion = 'DESCRIBE'
    def esInsert(self):
        self.__instruccion = 'INSERT'
    def esSelect(self):
        self.__instruccion = 'SELECT'
    def esDelete(self):
        self.__instruccion = 'DELETE'
    def esUpdate(self):
        self.__instruccion = 'UPDATE'
    def construirConsulta(self, parametrosPrincipales, condicion, union, orden,  limite):
        if not self.__instruccion: raise ErrorMalaSintaxisSQL("No se ha definido una clausula principal.")
        if self.__instruccion == 'INSERT':
            if condicion or union or limite: raise ErrorMalaSintaxisSQL("Las instrucciones INSERT no pueden tener clausulas WHERE, JOIN o LIMIT.")
        return self.__instruccion + '\n' + parametrosPrincipales + union + condicion + orden + limite + ';'


class Consulta():
    '''
    Clase que permite generar consultas SQL de forma programática. Las consultas se construyen concatenando
    las clausulas principales (SELECT, DELETE, INSERT, UPDATE) y las clausulas secundarias (WHERE, JOIN). Luego
    se espera que el objeto sea convertido a string para obtener la consulta SQL.


    METODOS PUBLICOS
    - SELECT(tabla : str, columnas : list[str] columnasSecundarias: Optional[Dict[str, List[str]] ] = {}) -> Self
    - DELETE(tabla : str) -> Self
    - INSERT(tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self
    - UPDATE(tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self
    - WHERE(tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]) -> Self
    - JOIN(tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER) -> Self
    - LIMIT(desplazamiento: int  , limite : int) -> Self
    Aclaracion: Los metodos From, Set y LIMIT no son metodos publicos, ya que son llamados internamente por los metodos que invocan clausulas principales.

    ATRIBUTOS PUBLICOS
    - TipoCondicion: Enumeracion que contiene los tipos de condiciones posibles.
    - TipoUnion: Enumeracion que contiene los tipos de joins posibles.

    EJEMPLOS DE USO:


    > consulta = Consulta().SELECT(tabla='Usuarios', columnas=['nombreUsuario', 'correo']).WHERE(id=1).LIMIT(10, 5)
    > print(consulta)


    SELECT 
    Usuarios.nombreUsuario, Usuarios.correo
    FROM Usuarios
    WHERE Usuarios.id = 1
    LIMIT 10, 5
    ;

    > consulta = Consulta().DELETE(tabla='Usuarios').WHERE(id=1)
    > print(consulta)

    DELETE 
    FROM Usuarios
    WHERE Usuarios.PRIMARY_KEY != 'NULL'
    AND Usuarios.id = 1
    ;

    > consulta = Consulta().INSERT(tabla='Usuarios', nombreUsuario='Juan')

    > consulta = Consulta().SELECT(tabla='Usuarios', columnas=['nombreUsuario', 'correo'], columnasSecundarias={'Discos': 'autor'})
    > consulta.JOIN(tablaSecundaria='Discos', columnaPrincipal='esPremium', columnaSecundaria ='esPremium', tipoUnion=TipoUnion.INNER)
    > print(consulta)

    SELECT Usuarios.nombreUsuario, Usuarios.correo, Discos.a, Discos.u, Discos.t, Discos.o, Discos.r
    FROM Usuarios
    INNER JOIN Discos ON Usuarios.esPremium = Discos.esPremium
    ;

    CASOS DE ERROR:

    La clase levanta errores de tipo ErrorMalaSintaxisSQL en los siguientes casos:
    - Se intenta invocar una clausula principal (SELECT, DELETE, INSERT, UPDATE) más de una vez.
    - Se intenta convertir a string sin clausula principal
    - Se intenta pedir columnas secundarias de una tabla que no ha sido unida.

    La clase levanta errores de tipo ErrorMalaSolicitud en los siguientes casos:

    CASOS
    
    
    '''

    __slots__ = \
    (   '__parametros_principales',
        '__instruccionPrincipal',
        '__tabla_principal',
        '__tablas_secundarias',
        '__condicion',
        '__union',
        '__orden',
        '__limite',
        )

    

    def __init__(self):
        self.reiniciar()

    def SELECT(self, tabla : str, columnas : list[str], columnasSecundarias: Optional[dict[str, list[str]] ] = {}) -> Self:
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esSelect()
        self.__parametros_principales = self.etiquetar(tabla, columnas)
        for t2, c2 in columnasSecundarias.items():
            self.__tablas_secundarias[t2] = 0
            self.__parametros_principales += ', ' + self.etiquetar(t2, c2) 
        self.__parametros_principales += '\n'
        self.__FROM(tabla)
        return self
    def DESCRIBE(self: Self, tabla :str) -> Self:
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esDescribe()
        self.__parametros_principales += self.__tabla_principal
        return self
    def DELETE(self, tabla : str):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esDelete()
        self.__FROM(tabla)
        self.WHERE(TipoCondicion.NO_ES, id = None)
        return self
    def INSERT(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esInsert()
        self.__parametros_principales = 'INTO ' + tabla + '\n'
        self.__SET(**asignaciones)
        return self
    def UPDATE(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esUpdate()
        self.__parametros_principales = tabla + '\n'
        self.__SET(**asignaciones)
        self.WHERE(TipoCondicion.NO_ES, id = None)
        return self
    def WHERE(self, tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]):
        def _adaptar(valor):
            if tipoCondicion == TipoCondicion.EN:
                return "(" + ", ".join(self.adaptar(v) for v in valor) + ")"
            return self.adaptar(valor, parecido=tipoCondicion == TipoCondicion.PARECIDO)
        condiciones : str = '   AND '.join(f"{self.etiquetar(self.__tabla_principal, [columna]) } {tipoCondicion} {_adaptar(valor)}" for columna, valor in columnaValor.items())
        if not condiciones: return self
        if not self.__condicion: self.__condicion = f'WHERE {condiciones}\n'
        else: self.__condicion += f' AND {condiciones}\n'
        return self
    def ORDER_BY(self, orden : [dict[str, TipoOrden]]):
        if not orden: return self
        orden : str = ', '.join(f"{self.etiquetar(self.__tabla_principal,[columna])} {direccion}" for columna, direccion in orden.items())        
        if not self.__orden: self.__orden = f'ORDER BY {orden}\n'
        else: self.__orden += f' , {orden}\n'
        return self

    
    def JOIN(self, tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER):
        self.__tablas_secundarias[tablaSecundaria] = 1
        nuevoJoin : str = tipoUnion +  ' JOIN ' + tablaSecundaria + ' ON ' + self.etiquetar(self.__tabla_principal, [columnaPrincipal]) + ' = ' + self.etiquetar(tablaSecundaria, [columnaSecundaria]) + '\n'
        self.__union += nuevoJoin        
        return self
    
    def LIMIT(self, desplazamiento: int  , limite : int):
        if self.__limite : raise ErrorMalaSintaxisSQL("La clausula LIMIT ya ha sido definida.")
        self.__limite  =  'LIMIT ' + str(desplazamiento) + ', ' + str(limite) + '\n'
        return self

    @property
    def tabla(self) -> str:
        return self.__tabla_principal

    def __FROM(self, tabla : str):
        self.__parametros_principales += 'FROM ' + tabla + '\n'
        return self
    def __SET(self, **columnaValor : Unpack[dict[str, Any]]):
        asignaciones = '\n, '.join(f"{self.etiquetar(self.__tabla_principal, [columna]) } = {self.adaptar(valor)}" for columna, valor in columnaValor.items())
        self.__parametros_principales += f'SET {asignaciones}\n'
        return self

    
    
    def etiquetar(self, tabla: str, columnas : list[str]) -> str:
        """Recibe una tabla y columnas. devuelve cada columna en el namespace de la tabla"""
        return ', '.join([tabla + '.' + columna  for columna in columnas])

    def adaptar(self, valor : Any, parecido : bool = False) -> str:
        return formatearValorParaSQL(valor, parecido=parecido)

    def reiniciar(self):
        self.__instruccionPrincipal = InstruccionPrincipal()
        self.__parametros_principales = ''
        self.__condicion = ''
        self.__union = ''
        self.__orden = ''
        self.__limite = ''

        self.__tabla_principal = ''
        self.__tablas_secundarias = {}

    
    def __str__(self):
        if not self.__parametros_principales: raise ErrorMalaSintaxisSQL("No se ha definido una clausula principal.") 
        for tabla, valor in self.__tablas_secundarias.items():
            if valor == 0:
                raise ErrorMalaSintaxisSQL(f"La tabla {tabla} no ha sido unida.")
        
        return self.__instruccionPrincipal.construirConsulta(self.__parametros_principales, self.__condicion, self.__union, self.__orden, self.__limite)
        


def _extraer_tabla(sql: str) -> str | None:
    tokens = sql.split()
    if not tokens:
        return None
    verbo = tokens[0].upper()
    try:
        if verbo in ('INSERT', 'REPLACE') and tokens[1].upper() == 'INTO':
            return tokens[2].strip('`;,')
        if verbo in ('DELETE', 'TRUNCATE') and tokens[1].upper() in ('FROM', 'TABLE'):
            return tokens[2].strip('`;,')
        if verbo == 'UPDATE':
            return tokens[1].strip('`;,')
        if verbo == 'SELECT':
            idx = sql.upper().find('FROM ')
            if idx != -1:
                return sql[idx + 5:].split()[0].strip('`; ,')
        if verbo in ('CREATE', 'ALTER', 'DROP') and len(tokens) > 2:
            idx = 2
            while idx < len(tokens) and tokens[idx].upper() in ('IF', 'NOT', 'EXISTS'):
                idx += 1
            return tokens[idx].strip('`;,') if idx < len(tokens) else None
    except IndexError:
        pass
    return None


def _intentar_auditar(bdd: 'BaseDeDatos_MySQL', sql: str, tabla_objetivo: str | None = None) -> None:
    import chastack_bdd.auditoria as _auditoria
    if _auditoria._auditando.get():
        return
    if _auditoria._tabla_auditoria is None:
        return
    tokens = sql.split()
    primer_token = tokens[0].upper() if tokens else ''
    es_mutacion = primer_token in ('INSERT', 'UPDATE', 'DELETE')
    es_lectura = primer_token == 'SELECT'
    if not es_mutacion and not (es_lectura and _auditoria._trazar_lecturas):
        return
    if tabla_objetivo is None:
        tabla_objetivo = _extraer_tabla(sql)
    token = _auditoria._auditando.set(True)
    try:
        audit_sql = (
            f"INSERT INTO {_auditoria._tabla_auditoria} (tabla_objetivo, operacion, consulta) "
            f"VALUES ({formatearValorParaSQL(tabla_objetivo)}, {formatearValorParaSQL(primer_token)}, {formatearValorParaSQL(sql)})"
        )
        bdd.ejecutar(audit_sql)
    except Exception as exc:
        logger.warning("Auditoría: no se pudo registrar evento en '%s': %s", tabla_objetivo or '?', exc)
    finally:
        _auditoria._auditando.reset(token)


class ConfigMySQL(metaclass=Solteron):

    __slots__ = (
        '__HOST',  
        '__USUARIO',  
        '__CONTRASENA',  
        '__NOMBRE_BDD'
    )

    def __init__(self, host, usuario, contrasena, bdd):
        self.__HOST = host
        self.__USUARIO = usuario
        self.__CONTRASENA = contrasena
        self.__NOMBRE_BDD = bdd
    @property
    def PARAMETROS_CONEXION(self) -> dict: 
        return \
        {
            "host" : self.__HOST,
            "user" : self.__USUARIO,
            "password" : self.__CONTRASENA,
            "database" : self.__NOMBRE_BDD,
            "use_pure" : False
        }

    @property
    def OPCION_CURSOR(self) -> dict:
        return \
        {
           "dictionary" : True,
           "named_tuple" : False,   
        }

class BaseDeDatos_MySQL():
    __slots__ = \
    (
        "__config",
        "__conexion",
        "__cursor",
        "__consulta"
    )
    def __init__(self, configuracion : ConfigMySQL = None) -> None:
        self.__conexion = None
        self.__cursor = None
        self.configurar(configuracion)
        self.__consulta = Consulta()
    
    def configurar(self, configuracion : ConfigMySQL = None) -> None:
        if configuracion:
            self.__config = configuracion
            return self
        # Agregar comportamiento usando las variables de ambiente

    def conectar(self) -> Self:
        if self.__conexion: return self
        self.__conexion = connect(**self.__config.PARAMETROS_CONEXION)
        self.__cursor = self.__conexion.cursor(buffered=True, **self.__config.OPCION_CURSOR)
        return self

    def desconectar(self) -> None:
        if self.__cursor: self.__cursor.close()
        if self.__conexion: self.__conexion.close()
        self.__cursor = None
        self.__conexion = None
    
    def reconectar(self) -> Self:
        self.desconectar()
        self.conectar()
        return self
    
    def DESCRIBE(self: Self, tabla :str) -> Self:
        self.__consulta.DESCRIBE(tabla)
        return self 
    def SELECT(self, tabla : str, columnas : list[str], columnasSecundarias: Optional[dict[str, list[str]] ] = {}) -> Self:
        self.__consulta.SELECT(tabla, columnas, columnasSecundarias)
        return self
    def DELETE(self, tabla : str) -> Self: 
        self.__consulta.DELETE(tabla)
        return self
    def INSERT(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self: 
        self.__consulta.INSERT(tabla, **asignaciones)
        return self
    def UPDATE(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self: 
        self.__consulta.UPDATE( tabla, **asignaciones)
        return self
    def WHERE(self, tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]) -> Self: 
        self.__consulta.WHERE(tipoCondicion, **columnaValor)
        return self
    def ORDER_BY(self, orden : [dict[str, TipoOrden]]):
        self.__consulta.ORDER_BY(orden)
        return self
    def JOIN(self,   tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER) -> Self: 
        self.__consulta.JOIN(tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion)
        return self
    def LIMIT(self, desplazamiento: int  , limite : int) -> Self: 
        self.__consulta.LIMIT(desplazamiento, limite)
        return self
   
    @sobrecargar
    def ejecutar(self, consulta : Union[Consulta,str]) -> Optional[list[Resultado]] :
        if isinstance(consulta,Consulta):
            consulta = str(consulta)
        try:
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except ErrorBDD as e:
            ###print(f"[ERROR] {e}")
            self.reconectar()
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except AttributeError as e:
            ###print(f"[ERROR] {e}")
            self = BaseDeDatos_MySQL()
            self.conectar()
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except Exception as f:
            raise type(f)(f"No se pudo completar la consulta.\n Es probable que la consulta incluya carácteres prohibidos. \n {consulta.encode('utf-8').decode('unicode_escape')}\n") from f
        _intentar_auditar(self, consulta)
        return self

    @sobrecargar
    def ejecutar(self) -> Optional[list[Resultado]] :
        try:
            sql = str(self.__consulta)
            tabla_objetivo = self.__consulta.tabla
            try:
                self.__cursor.execute(sql)
                self.__conexion.commit()
            except ErrorBDD as e:
                ###print(f"[ERROR] {e}")
                self.reconectar()
                self.__cursor.execute(sql)
                self.__conexion.commit()
            except AttributeError as e:
                ###print(f"[ERROR] {e}")
                self = BaseDeDatos_MySQL(self.__config)
                self.conectar()
                self.__cursor.execute(sql)
                self.__conexion.commit()
            except Exception as f:
                raise type(f)(f"No se pudo completar la consulta.\n Es probable que la consulta incluya carácteres prohibidos. \n {sql.encode('utf-8').decode('unicode_escape')}\n") from f
        finally:
            self.__consulta.reiniciar()
        _intentar_auditar(self, sql, tabla_objetivo)
        return self
   
    def devolverIdUltimaInsercion(self : Self) -> Optional[int]:
        return self.__cursor.lastrowid
        
    def devolverResultados(self, cantidad : Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        resultados = self.__cursor.fetchall()
        
        if not resultados: return None
        elif cantidad is None: return resultados
        elif cantidad == 0: return []
        elif cantidad > 0: return resultados[0:cantidad-1]
        else: raise IndexError("Se solicitó una cantidad negativa de resultados, lo cual es un sinsentido.")
    def devolverUnResultado(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve el primer resultado de la última consulta.
        """
        return self.__cursor.fetchone()
        
    # Estados
    def estaConectado (self):
            return self.__conexion.is_connected() if self.__conexion else False



  # with BaseDeDatos() as bdd
    def __enter__(self) -> 'BaseDeDatos_MySQL':
        if self.__conexion is None:
            return self.conectar()
        # ###print(f"[DEBUG] Entrando {self.__cursor=}{self.__conexion=}{self.__pool=}")
        return self

    def __exit__(self, exc_type,excl_val,exc_tb) -> None:
        # ###print(f"[DEBUG] Saliendo {self.__cursor=}{self.__conexion=}{self.__pool=}")
        self.desconectar()
