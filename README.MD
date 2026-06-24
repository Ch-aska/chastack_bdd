

# chastack_bdd

[![Hecho por Chaska](https://img.shields.io/badge/hecho_por-Ch'aska-303030.svg)](https://cajadeideas.ar)
[![Versión: 0.8.5](https://img.shields.io/badge/version-v0.8.5-green.svg)](https://github.com/hernanatn/github.com/hernanatn/bdd.py/releases/latest)
[![Verisón de Python: 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://www.python.org/downloads/release/python-3130/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-lightgrey.svg)](LICENSE)

`chastack_bdd` es una librería de Python que permite definir clases que, en tiempo de ejecución, se poblan automáticamente con los atributos definidos en las tablas SQL homónimas. Se utiliza un enfoque de metaprogramación para que, al declarar una clase con `metaclass=Tabla`, la clase resultante herede de `Registro` y adquiera todos los métodos y comportamientos necesarios para interactuar con la base de datos de manera transparente y segura.

La inicialización de las clases es "vaga": la estructura de la tabla se consulta y se refleja en la clase solo cuando se instancia por primera vez o cuando se invocan ciertos métodos de clase. Esto garantiza que los atributos (`__slots__`) estén sincronizados con la base de datos y que los campos no modificables (como `id`, `fecha_carga`, `fecha_modificacion`) estén protegidos contra escritura directa.

> [!TIP]   
> Todas las clases creadas con `metaclass=Tabla` aceptan el parámetro especial `debug`, que permite obtener información de diagnóstico sobre la inicialización, instanciación y otros eventos internos, facilitando el manejo de errores y la depuración.

Se provee un protocolo de base de datos (`ProtocoloBaseDeDatos`) para que el usuario pueda implementar su propia abstracción de acceso a datos. Además, se incluye una implementación acoplada a MySQL lista para usar.

---

## Documentación

| Tema                        | Enlace                                                                  | Descripción breve                                      |
|-----------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------|
| 📑 Referencia de la API      | [Referencia de la API](./documentacion/referencia.md)                               | Métodos, clases y firmas públicas                      |
| 🧑‍💻 Ejemplos de uso         | [Ejemplos de uso](./documentacion/ejemplos.md)                                     | Casos prácticos, básicos y avanzados                   |
| 🏗️ Creación de modelos       | [Creación de modelos](./documentacion/registro.md)                                 | Cómo definir y manipular modelos con metaclass=Tabla   |
| 👤 Gestión de usuarios       | [Gestión de usuarios](./documentacion/usuario.md)                                  | Modelos de usuario, autenticación y seguridad          |
| 🔌 Extensión a otros motores | [Extensión a otros motores de BDD](./documentacion/protocolo_bdd.md)               | Implementar soporte para otros motores de base de datos|
| 🗃️ Requisitos de las tablas  | [Requisitos de las tablas SQL](./documentacion/requisitos_tablas.md)               | Estructura mínima y convenciones de las tablas         |

---

## ¿Qué es chastack_bdd?

chastack_bdd permite definir clases Python que representan tablas SQL, poblando automáticamente sus atributos y métodos según la estructura de la base de datos. Utiliza metaprogramación avanzada para garantizar sincronización, protección de campos críticos y soporte para relaciones complejas.

**Modelos automáticos**: Las clases declaradas con `metaclass=Tabla` adquieren dinámicamente los atributos y métodos necesarios para operar sobre la tabla homónima.  
**Relaciones y consultas**: Se provee soporte nativo para relaciones muchos a muchos, así como para consultas avanzadas y ordenamientos personalizados.  
**Gestión de usuarios**: Se incluye una clase base `Usuario` que implementa los mecanismos necesarios para autenticación y gestión segura de credenciales.  
**Backend desacoplado**: La interacción con la base de datos se realiza a través de un protocolo `ProtocoloBaseDeDatos`, permitiendo utilizar la implementación incluida para MySQL o desarrollar una propia.

---

## Ejemplo mínimo
Primero se debe definir (y crear) la tabla para la cual se quiere producir el model (debe ajustarse al requisito mínimo de `Registro`).
```sql
CREATE TABLE Cliente (
    id INT PRIMARY KEY AUTO_INCREMENT,
    , fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
    , fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    , email VARCHAR(100) NOT NULL
    , nombre VARCHAR(100) NOT NULL
);
```
Luego se debe crear la configuración y conexión para la base de datos, en el ejemplo usaremos MySQl, pero se puede utilizar cualquier abstracción que se ajuste al protocolo.

```python
from chastack_bdd importConfigMySQL, BaseDeDatos_MySQL

config = ConfigMySQL(
    host="localhost",
    usuario="root_o_usuario",
    contrasena="contraseña_root_o_usuario",
    bdd="base_a_usar"
)

bdd = BaseDeDatos_MySQL(config)

```

Finalmente definimos la clase en Python, sin necesidad de declarar sus atributos.

```python
from chastack_bdd import Tabla, Registro

class Cliente(metaclass=Tabla):
    pass

nuevo_cliente = Cliente(bdd, {"nombre": "Ana", "email": "ana@ejemplo.com"})
nuevo_cliente.guardar()

cliente_1 = Cliente(bdd, id=1)
print("Nombre:", cliente_1.nombre)
print("Email:", cliente_1.email)
print("Fecha de carga:", cliente_1.fecha_carga)

for columna, valor in cliente_1:
    print(f"{columna}: {valor}")
```

Para ejemplos avanzados, ver [Ejemplos de uso](./documentacion/ejemplos.md).

---

## Instalación

#### Aislada
```bash
pip install chastack_bdd
```

#### Como parte de [chastack]()
```bash
pip install chastack
```
---

## Licencia

MIT. Ver [LICENSE](./LICENSE).
