# Ejemplos de uso de chastack_bdd

A continuación se presentan ejemplos de uso que ilustran las capacidades intermedias y avanzadas de la librería, diferenciando entre la definición de modelos con `metaclass=Tabla` y el caso especial de usuarios.

---

## Definición de modelos con `metaclass=Tabla`

Definición de nuevas clases modelo que reflejan tablas SQL homónimas.

### Ejemplo básico

```python
from chastack_bdd import Tabla, Registro

class Cliente(metaclass=Tabla):
    pass

# Al instanciar, se poblará automáticamente con los campos de la tabla 'Cliente' en la base de datos.
# Se puede pasar debug=True para ver mensajes de diagnóstico:
cliente = Cliente(bdd, id=1, debug=True)
```

### Inicialización y consulta de registros

```python
bdd = BaseDeDatos_MySQL(configuracion)
cliente = Cliente(bdd, id=1, debug=True)  # Mensajes de diagnóstico habilitados
print(cliente.nombre, cliente.email)

# Iterar sobre columnas y valores
for columna, valor in cliente:
    print(f"{columna}: {valor}")
```

### Creación y guardado de registros

```python
nuevo_cliente = Cliente(bdd, {"nombre": "Ana", "email": "ana@ejemplo.com"})
nuevo_cliente.guardar()
```

### Uso de relaciones muchos a muchos

```python
class Grupo(metaclass=Tabla):
    pass

class ClienteGrupo(metaclass=TablaIntermedia):
    tabla_primaria = Cliente
    tabla_secundaria = Grupo

cliente.añadirRelacion(grupo, 'Grupo')
```

### Consultas avanzadas con filtros y orden

```python
clientes = Cliente.devolverRegistros(bdd, cantidad=10, orden={"nombre": TipoOrden.ASC}, email="%@gmail.com")
for c in clientes:
    print(c)
    # Iterar sobre cada registro
    for columna, valor in c:
        print(f"{columna}: {valor}")
```

### Consultas con IN y expresiones SET

`TipoCondicion.EN` genera una cláusula `WHERE ... IN (...)`. El valor debe ser un iterable:

```python
from chastack_bdd import TipoCondicion

ids = [1, 2, 3, 5, 8]
clientes = bdd.SELECT("Cliente", ["id", "nombre", "email"]) \
    .WHERE(TipoCondicion.EN, id=ids) \
    .ejecutar() \
    .devolverResultados()
```

Se puede combinar con otras condiciones encadenando `.WHERE()`:

```python
resultados = bdd.SELECT("Producto", ["id", "nombre", "stock"]) \
    .WHERE(categoria_id=7) \
    .WHERE(TipoCondicion.EN, estado=["disponible", "reservado"]) \
    .WHERE(TipoCondicion.MAYOR, stock=0) \
    .ejecutar() \
    .devolverResultados()
```

`ExprSQL` permite incluir expresiones SQL en cláusulas `SET` de `UPDATE` sin que sean escapadas:

```python
from chastack_bdd import ExprSQL

# Incremento atómico
bdd.UPDATE("Producto", visitas=ExprSQL("visitas + 1")) \
   .WHERE(id=42) \
   .ejecutar()

# Función SQL
bdd.UPDATE("Inventario", stock=ExprSQL("GREATEST(0, stock - 1)")) \
   .WHERE(TipoCondicion.EN, producto_id=[10, 11, 12]) \
   .ejecutar()
```

> [!WARNING]
> `ExprSQL` no aplica ningún escape. Usar solo con literales definidos en el código, nunca con datos del usuario.

---

## Modelos de usuario con autenticación

Para modelos de usuario, se debe heredar de `Usuario` y usar `metaclass=Tabla`:

```python
from chastack_bdd import Tabla, Usuario

class MiUsuario(Usuario, metaclass=Tabla):
    pass

usuario = MiUsuario(bdd, correo="ana@ejemplo.com", contrasena="secreta")
usuario.guardar()

# Autenticación
usuario_autenticado = MiUsuario.ingresar(bdd, nombre_usuario="ana@ejemplo.com", contrasena="secreta")

# Iterar sobre los campos del usuario
for columna, valor in usuario_autenticado:
    print(f"{columna}: {valor}")
```

---

## Ejemplo avanzado

```python
from chastack_bdd import Tabla, TablaIntermedia, Registro, Usuario, TipoOrden
from decimal import Decimal

# Modelo con campo ENUM y relación muchos a muchos
class Producto(metaclass=Tabla):
    pass  # La tabla SQL debe tener un campo 'estado' ENUM('disponible','agotado','discontinuado')

class Categoria(metaclass=Tabla):
    pass

class ProductoCategoria(metaclass=TablaIntermedia):
    tabla_primaria = Producto
    tabla_secundaria = Categoria

class Cliente(metaclass=Tabla):
    pass

class Compra(metaclass=Tabla):
    pass

# Usuario avanzado
class MiUsuario(Usuario, metaclass=Tabla):
    pass

bdd = BaseDeDatos_MySQL(config)

# Crear productos y categorías
p1 = Producto(bdd, {"nombre": "Notebook", "precio": Decimal("1200.00"), "estado": "disponible"})
p2 = Producto(bdd, {"nombre": "Mouse", "precio": Decimal("25.00"), "estado": "agotado"})
c1 = Categoria(bdd, {"nombre": "Electrónica"})
c2 = Categoria(bdd, {"nombre": "Oficina"})
p1.guardar()
p2.guardar()
c1.guardar()
c2.guardar()

# Relacionar productos y categorías
p1.añadirRelacion(c1, 'Categoria')
p1.añadirRelacion(c2, 'Categoria')
p1.guardar()

# Crear usuario y cliente
usuario = MiUsuario(bdd, correo="cliente@ejemplo.com", contrasena="segura123")
usuario.guardar()
cliente = Cliente(bdd, {"nombre": "Juan", "email": "juan@ejemplo.com"})
cliente.guardar()

# Registrar una compra
compra = Compra(bdd, {"cliente_id": cliente.id, "producto_id": p1.id, "cantidad": 2, "total": Decimal("2400.00")})
compra.guardar()

# Consultas avanzadas
productos = Producto.devolverRegistros(bdd, cantidad=5, orden={"precio": TipoOrden.DESC}, estado="disponible")
for prod in productos:
    print(f"Producto: {prod.nombre} - Estado: {prod.estado}")
    for columna, valor in prod:
        print(f"  {columna}: {valor}")

# Autenticación avanzada
usuario_autenticado = MiUsuario.ingresar(bdd, nombre_usuario="cliente@ejemplo.com", contrasena="segura123")
print("Sesión iniciada:", usuario_autenticado.id_sesion)

@sobrecargar
def procesar_registro(registro: Producto):
    print("Procesando producto", registro.nombre)

@sobrecargar
def procesar_registro(registro: Cliente):
    print("Procesando cliente", registro.nombre)

procesar_registro(p1)
procesar_registro(cliente)
```

---

> [!NOTE]      
> Cualquier clase que herede de `Registro` permite iterar sobre sus columnas y valores con `for columna, valor in un_registro:`. Para usuarios, siempre se debe heredar de `Usuario` y no instanciarlo directamente.

---

## Auditoría de operaciones SQL

Una sola llamada al inicio activa el log de toda operación SQL que pase por el ORM:

```python
import chastack_bdd as chbdd
chbdd.configurar_auditoria()                     # mutaciones (INSERT/UPDATE/DELETE)
chbdd.configurar_auditoria(trazar_lecturas=True) # también SELECT
```

Cubre tanto el builder fluido como el path de SQL crudo (`ejecutar(str)`). La tabla `EventoAuditoria` debe existir:

```sql
CREATE TABLE EventoAuditoria (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    fecha_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tabla       VARCHAR(64),
    operacion   VARCHAR(20) NOT NULL,
    consulta    TEXT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

`tabla` es nullable — para SQL crudo donde el nombre de tabla no siempre se puede determinar. `operacion` es `VARCHAR(20)` en lugar de ENUM para cubrir cualquier verbo SQL (`TRUNCATE`, `ALTER`, etc.).

A partir de esa llamada, cada operación ejecutada a través del ORM genera automáticamente un registro en `EventoAuditoria`. No se requiere ninguna acción adicional en los callsites.