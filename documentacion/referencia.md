# Referencia técnica detallada de chastack_bdd

Este documento detalla la interfaz pública y privada de las principales clases de chastack_bdd. Se listan las firmas, tipos y una breve descripción técnica de cada método o atributo relevante.

---

## Interfaz pública

### Registro

> [!TIP]    
> Todos los métodos constructores de clases con `metaclass=Tabla` aceptan el parámetro especial `debug: bool = False`.

#### Métodos de instancia
- `guardar() -> int`: Guarda el registro en la base de datos (crea o actualiza).
- `añadirRelacion(registro: Registro, tabla: str) -> None`: Agrega una relación muchos a muchos.
- `obtenerMuchos(tabla: str) -> dict[int, Registro]`: Devuelve registros relacionados.
- `borrarRelacion(registro: Registro, tabla: str) -> None`: Elimina una relación muchos a muchos.
- `__str__() -> str`: Representación tabular del registro.
- `__iter__() -> Iterator[tuple[str, Any]]`: Itera sobre (columna, valor) de los campos públicos.

#### Métodos de clase
- `devolverRegistros(bdd: ProtocoloBaseDeDatos, *, cantidad: int = 1000, indice: int = 0, orden: Optional[dict[str, TipoOrden]] = None, filtrosJoin: Optional[dict[str, str]] = None, **condiciones) -> tuple[Registro]`: Consulta registros.
- `atributos() -> list[str]`: Lista de atributos públicos.
- `inicializar(bdd: ProtocoloBaseDeDatos) -> None`: Fuerza la inicialización de la clase.

#### Métodos especiales
- `__init__(bdd: ProtocoloBaseDeDatos, valores: dict, *, debug: bool = False)`
- `__init__(bdd: ProtocoloBaseDeDatos, id: int, *, debug: bool = False)`

---

### Tabla y TablaIntermedia (metaclases)
- Uso indirecto: permiten la inicialización "vaga" y la sincronización automática de atributos.
- No exponen métodos públicos directos para el usuario final.

---

### `Usuario`

> [!TIP]    
> Todos los métodos constructores de clases con `metaclass=Tabla` aceptan el parámetro especial `debug: bool = False`.

#### Constructor
- `__init__(bdd, correo: str, contrasena: str, nombre_usuario: str = None, *, debug=False)`

#### Métodos de clase
- `registrar(bdd, correo: str, contrasena: str, nombre_usuario: str = None, **otros_campos) -> Usuario`: Registra un usuario.
- `ingresar(bdd, nombre_usuario: str, contrasena: str) -> Usuario`: Autentica por usuario/correo y contraseña.
- `ingresar(bdd, id_sesion: str) -> Usuario`: Autentica por id de sesión.

#### Métodos de instancia
- `cerrarSesion() -> None`: Cierra la sesión del usuario.
- `cambiarContraseña(contrasena_nueva: str) -> Self`: Cambia la contraseña.

#### Utilidades estáticas
- `encriptarContraseña(contrasena: str, sal: bytes = None) -> tuple[bytes, bytes]`

---

## Tipos y enumeraciones (`tipos`)

### `TipoCondicion`

Enumeración de operadores de condición para usar en `WHERE()`.

| Valor | SQL generado | Uso |
|---|---|---|
| `TipoCondicion.IGUAL` | `=` | Igualdad (por defecto) |
| `TipoCondicion.DIFERENTE` | `!=` | Desigualdad |
| `TipoCondicion.PARECIDO` | `LIKE` | Coincidencia parcial con `%` |
| `TipoCondicion.MAYOR` | `>` | Mayor que |
| `TipoCondicion.MENOR` | `<` | Menor que |
| `TipoCondicion.MAYOR_O_IGUAL` | `>=` | Mayor o igual |
| `TipoCondicion.MENOR_O_IGUAL` | `<=` | Menor o igual |
| `TipoCondicion.ES` | `IS` | IS NULL / IS TRUE |
| `TipoCondicion.NO_ES` | `IS NOT` | IS NOT NULL |
| `TipoCondicion.EN` | `IN` | Pertenencia a lista — el valor debe ser un iterable |

---

## Utilidades (`utiles`)

### `ExprSQL(str)`

Subclase de `str` que marca una cadena como expresión SQL cruda. `formatearValorParaSQL` la interpola sin escapar ni entrecomillar, lo que permite usar expresiones en cláusulas `SET` de `UPDATE`:

```python
# SET Fragmento.refcount = refcount + 1
conn.UPDATE("Fragmento", refcount=ExprSQL("refcount + 1"))

# SET Fragmento.refcount = GREATEST(0, refcount - 1)
conn.UPDATE("Fragmento", refcount=ExprSQL("GREATEST(0, refcount - 1)"))
```

> [!WARNING]
> `ExprSQL` no aplica ningún escape. Nunca construir una `ExprSQL` con datos provenientes del usuario — solo con literales definidos en el código.

### `_escaparParaMySQL(texto: str) -> str`

Escapa caracteres especiales para SQL concatenado en MySQL. MySQL interpreta backslashes como caracteres de escape por defecto (a menos que esté activado `NO_BACKSLASH_ESCAPES`). Esta función escapa los caracteres que rompen queries SQL construidas por concatenación de strings.

> [!IMPORTANT]
> El orden de los reemplazos es crítico. Backslash se escapa **primero** para evitar doble-escape.

| Carácter | Escape | Motivo |
|---|---|---|
| `\` | `\\` | Carácter de escape de MySQL |
| `'` | `''` | Delimitador de strings SQL |
| `\n` | `\n` (literal) | Newline |
| `\r` | `\r` (literal) | Carriage return |
| `\0` | _(eliminado)_ | Null byte — corta strings en MySQL |
| `\t` | `\t` (literal) | Tab |

### `formatearValorParaSQL(valor: Any, html: bool = False, parecido: bool = False) -> str`

Formatea un valor de Python a una representación adecuada para SQL. Utiliza `_escaparParaMySQL` internamente para sanitizar valores de tipo `str`, `dict` y el fallback `str(valor)`. Los valores de tipo `ExprSQL` se devuelven sin modificar.

### `tipoSQLDesdePython(tipo_python: type) -> str`

Devuelve el tipo SQL correspondiente a un tipo de Python.

