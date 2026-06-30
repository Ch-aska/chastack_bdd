import unittest
from chastack_bdd.bdd import ConfigMySQL, BaseDeDatos_MySQL, _extraer_tabla
from chastack_bdd.tabla import Tabla, TablaIntermedia
from chastack_bdd.usuario import Usuario
from chastack_bdd.tipos import TipoOrden
from chastack_bdd.utiles import _escaparParaMySQL, formatearValorParaSQL
from chastack_bdd import configurar_auditoria
import chastack_bdd.auditoria as _auditoria_mod
from datetime import datetime, date, time
from decimal import Decimal
from sobrecargar import sobrecargar
import mysql.connector
from mysql.connector import errorcode, Error
import os
import traceback

CI = os.environ.get("CI", "false").lower() == "true"
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1") if CI else "localhost"
ROOT_P : str = os.environ.get('MYSQL_ROOT_PASSWORD')



def crearBaseDeDatos():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user="root",
        password=ROOT_P  
    )
    try:
        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS `chastack_bdd_pruebas`;")

        cursor.execute("""
            CREATE USER IF NOT EXISTS 'usuario_de_prueba'@'%'
            IDENTIFIED BY 'pRU3b4s!1?2@3$4';
        """)

        privilegios = ['SELECT', 'UPDATE', 'DELETE', 'INSERT', 'EXECUTE']
        for priv in privilegios:
            cursor.execute(f"""
                GRANT {priv} ON chastack_bdd_pruebas.* TO 'usuario_de_prueba'@'%';
            """)

        cursor.execute("FLUSH PRIVILEGES;")
        #print("Base de datos y usuario creados con éxito.")
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
def crearYPoblarTablas():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user="root",
        password=ROOT_P,
        database="chastack_bdd_pruebas"
    )
    try:
        cursor = conn.cursor()

        # Tabla Cliente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Cliente (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                nombre VARCHAR(150) NOT NULL,
                apellido VARCHAR(150) NOT NULL,
                edad int NOT NULL,
                correo VARCHAR(150) NOT NULL,
                bio TEXT NOT NULL,
                url_img_principal VARCHAR(150)
            );
        """)

        # Tabla Nota
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Nota (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                titulo VARCHAR(150) NOT NULL,
                subtitulo VARCHAR(150) NOT NULL,
                cuerpo TEXT NOT NULL,
                resumen VARCHAR(250),
                url_img_principal VARCHAR(150)
            );
        """)

        # Tabla Tema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tema (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                nombre VARCHAR(150) NOT NULL
            );
        """)

        # Tabla Voz
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Voz (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                voz VARCHAR(150) NOT NULL
            );
        """)

        # Tabla TemaDeNota
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TemaDeNota (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                id_tema INT NOT NULL,
                id_nota INT NOT NULL,
                FOREIGN KEY (id_tema) REFERENCES Tema(id) ON DELETE CASCADE,
                FOREIGN KEY (id_nota) REFERENCES Nota(id) ON DELETE CASCADE
            );
        """)

        # Tabla VozDeNota
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VozDeNota (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                id_voz INT NOT NULL,
                id_nota INT NOT NULL,
                FOREIGN KEY (id_voz) REFERENCES Voz(id) ON DELETE CASCADE,
                FOREIGN KEY (id_nota) REFERENCES Nota(id) ON DELETE CASCADE
            );
        """)

        # Tabla Permiso
        # // cursor.execute("""
        # //     CREATE TABLE IF NOT EXISTS Permiso (
        # //         id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
        # //         fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        # //         fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        # //         rol VARCHAR(25)
        # //     );
        # // """)

        # Tabla Administrador (unificada con campos de Usuario)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Administrador (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                nombre VARCHAR(50) DEFAULT NULL,
                nombre_usuario VARCHAR(50) NOT NULL,
                correo VARCHAR(75) NOT NULL,
                contrasena VARBINARY(96) NOT NULL,
                sal VARBINARY(96) NOT NULL,
                rol ENUM('USUARIO','ADMINISTRADOR','SUPERUSUARIO') DEFAULT 'USUARIO' NOT NULL,
                fecha_ultimo_ingreso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                id_sesion VARCHAR(300) DEFAULT NULL,
                codigo_unico VARCHAR(300) DEFAULT NULL,
                UNIQUE KEY(nombre_usuario),
                UNIQUE KEY(correo),
                UNIQUE KEY(id_sesion)
            );
        """)

        # Tabla PermisosDeAdministrador
        ## cursor.execute("""
        ##     CREATE TABLE IF NOT EXISTS PermisosDeAdministrador (
        ##         id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
        ##         fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ##         fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        ##         id_administrador INT NOT NULL,
        ##         id_permiso INT NOT NULL,
        ##         CONSTRAINT PermisosDeAdministrador_ibfk_1 FOREIGN KEY (id_administrador) REFERENCES Administrador(id) ON DELETE CASCADE,
        ##         CONSTRAINT PermisosDeAdministrador_ibfk_2 FOREIGN KEY (id_permiso) REFERENCES Permiso(id) ON DELETE CASCADE,
        ##         UNIQUE KEY(administrador_permiso) (id_administrador, id_permiso)
        ##     );
        ## """)

        # Tabla para pruebas de auditoría (no usada por otros test cases)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RegistroSimple (
                id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
                fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                valor VARCHAR(100) NOT NULL
            );
        """)

        # Tabla de auditoría
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EventoAuditoria (
                id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                fecha_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                tabla_objetivo VARCHAR(64),
                operacion VARCHAR(20) NOT NULL,
                consulta TEXT NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        conn.commit()
        #print("Todas las tablas se han creado correctamente.")

    except Error as e:
        print("Error al crear las tablas:", e, '\n', traceback.format_exc())
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user="usuario_de_prueba",
        password="pRU3b4s!1?2@3$4",
        database="chastack_bdd_pruebas"
    )
    try:
        cursor = conn.cursor()

        # Inserciones en orden lógico
        cursor.execute("""
            INSERT INTO Tema (nombre) VALUES 
            ('Salud Pública'),
            ('Educación Rural'),
            ('Infraestructura'),
            ('Acceso a Medicamentos'),
            ('Cultura Local');
        """)

        cursor.execute("""
            INSERT INTO Nota (titulo, subtitulo, cuerpo, resumen, url_img_principal) VALUES 
            ('La salud en zonas rurales', 'Un desafío persistente', 'Texto extenso sobre salud rural...', 'Panorama de la salud rural', 'img/salud1.jpg'),
            ('Educación en parajes', 'Desigualdad educativa', 'Texto sobre educación...', 'Educación rural en cifras', 'img/edu1.jpg'),
            ('Medicamentos esenciales', 'Acceso limitado', 'Texto sobre acceso a medicamentos...', 'El acceso a los medicamentos esenciales', 'img/med1.jpg'),
            ('El rol del médico rural', 'Historias de vocación', 'Texto con entrevistas a médicos...', 'Testimonios rurales', 'img/medico1.jpg'),
            ('Cultura y salud', 'Interculturalidad médica', 'Texto sobre medicina y cultura...', 'Cruce entre saberes', 'img/cultura1.jpg');
        """)

        cursor.execute("""
            INSERT INTO TemaDeNota (id_tema, id_nota) VALUES 
            (1, 1), (2, 2), (4, 3), (1, 4), (5, 5);
        """)

        cursor.execute("""
            INSERT INTO Voz (voz) VALUES 
            ('Dr. Fernández'),
            ('Enfermera María'),
            ('Docente rural Juan'),
            ('Vecina Marta'),
            ('Promotor de salud Pablo');
        """)

        cursor.execute("""
            INSERT INTO VozDeNota (id_voz, id_nota) VALUES 
            (1, 1), (2, 1), (3, 2), (4, 4), (5, 5);
        """)


        cursor.execute("""
            INSERT INTO Administrador (nombre, nombre_usuario, contrasena, sal, correo) VALUES 
            ('Ana Pérez', 'admin1', UNHEX(SHA2('admin1',512)), UNHEX(SHA2('sal1',512)), 'admin1@mail.com'),
            ('Luis Gómez', 'admin2', UNHEX(SHA2('admin2',512)), UNHEX(SHA2('sal2',512)), 'admin2@mail.com'),
            ('Sofía Ríos', 'admin3', UNHEX(SHA2('admin3',512)), UNHEX(SHA2('sal3',512)), 'admin3@mail.com'),
            ('Carlos Díaz', 'admin4', UNHEX(SHA2('admin4',512)), UNHEX(SHA2('sal4',512)), 'admin4@mail.com'),
            ('Elena Ruiz', 'admin5', UNHEX(SHA2('admin5',512)), UNHEX(SHA2('sal5',512)), 'admin5@mail.com');
        """)

        # //cursor.execute("""
        # //    INSERT INTO Permiso (rol) VALUES 
        # //    ('superadmin'),
        # //    ('editor'),
        # //    ('moderador'),
        # //    ('analista'),
        # //    ('auditor');
        # //""")

        # //cursor.execute("""
        # //    INSERT INTO PermisosDeAdministrador (id_administrador, id_permiso) VALUES 
        # //    (1, 1), (2, 2), (3, 3), (4, 4), (5, 5);
        # //""")

        conn.commit()
        #print("¡Inserciones completadas con éxito!")

    except Error as e:
        print(f"Error al conectar o insertar:", e, '\n', traceback.format_exc())
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
def destruirBaseDeDatos():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user="root",
        password=ROOT_P
    )
    try:
        cursor = conn.cursor()

        cursor.execute("DROP DATABASE IF EXISTS `chastack_bdd_pruebas`;")
        cursor.execute("DROP USER IF EXISTS 'usuario_de_prueba'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        #print("Base de datos y usuario eliminados con éxito.")
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

CONFIG_BDD_PRUEBAS = ConfigMySQL(
            MYSQL_HOST,
            "usuario_de_prueba",
            "pRU3b4s!1?2@3$4",
            "chastack_bdd_pruebas",
        )

class RegistroSimple(metaclass=Tabla): ...
class Cliente(metaclass=Tabla):...

class PruebaRegistros(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)

    def test_crear_registro(self):
        cliente = Cliente(self.bdd,
        {
            'nombre': "Juan",
            'apellido': "Pelotas",
            'correo': "juan_pelotas@gmail.com",
            'edad': 70,
            "bio": 'una biografia aleatoria\nde juan pelotas.',
        })
        cliente.guardar()
        #print(cliente)
        self.assertIsNotNone(cliente.id)
        self.assertEqual(cliente.id,1)
        u = datetime.now().microsecond
        admin = Administrador(
            self.bdd,
            dict(
                nombre="Admin",
                nombre_usuario=f"admin{u}",
                contrasena="admin1234".encode('utf-8'),
                sal="asdadas".encode('utf-8'),
                rol=Usuario.TipoRol.SUPERUSUARIO,
                correo=f"admin{u}@fundacionzaffaroni.ar"
            )
        )
        admin.guardar()
        #print(admin)
        self.assertIsNotNone(admin.id)
        self.assertEqual(admin.nombre, "Admin")
        self.assertEqual(admin.rol, Usuario.TipoRol.SUPERUSUARIO)
        self.assertTrue(admin.verificarRol(Usuario.TipoRol.SUPERUSUARIO))
        self.assertTrue(admin.verificarRol(Usuario.TipoRol.ADMINISTRADOR))
        self.assertTrue(admin.verificarRol(Usuario.TipoRol.USUARIO))

class Administrador(Usuario,metaclass=Tabla):
    @sobrecargar
    def unMetodo(x: int): ...

    @sobrecargar
    def unMetodo(x: str): ...

class PruebaUsuario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)

    def test_devolver_administradores(self):
        admins = Administrador.devolverRegistros(
            self.bdd, cantidad=25, orden={"id": TipoOrden.DESC},
            correo="desarrollo@cajadeideas.ar"
        )
        self.assertIsInstance(admins, (list, tuple))
        for admin in admins:
            self.assertTrue(hasattr(admin, "nombre_usuario"))

    def test_registro_y_login_usuario(self):
        u = datetime.now().microsecond
        juan = Administrador.registrar(
            self.bdd,
            correo=f"juan@juan.juan{u}",
            contrasena="JuanJuan!1234",
            atributo_juan=7,
            rol=Usuario.TipoRol.USUARIO,
            nombre="juan"
        )
        self.assertIsNotNone(juan)
        juan.guardar()
        #print(juan)
        self.assertIsNotNone(juan.id)
        juan2 = juan.ingresar(self.bdd, f"juan@juan.juan{u}", "JuanJuan!1234")
        self.assertEqual(juan2.correo, f"juan@juan.juan{u}")
        self.assertEqual(juan2.rol, Usuario.TipoRol.USUARIO)
        self.assertFalse(juan2.verificarRol(Usuario.TipoRol.SUPERUSUARIO))
        self.assertFalse(juan2.verificarRol(Usuario.TipoRol.ADMINISTRADOR))
        self.assertTrue(juan2.verificarRol(Usuario.TipoRol.USUARIO))

    def test_crear_administrador(self):
        u = datetime.now().microsecond
        admin = Administrador(
            self.bdd,
            dict(
                nombre="Admin",
                nombre_usuario=f"admin{u}",
                contrasena="admin1234".encode('utf-8'),
                sal="asdadas".encode('utf-8'),
                rol=Usuario.TipoRol.ADMINISTRADOR,
                correo=f"admin{u}@fundacionzaffaroni.ar"
            )
        )
        admin.guardar()
        #print(admin)
        self.assertIsNotNone(admin.id)
        self.assertEqual(admin.nombre, "Admin")
        self.assertEqual(admin.rol, Usuario.TipoRol.ADMINISTRADOR)
        self.assertFalse(admin.verificarRol(Usuario.TipoRol.SUPERUSUARIO))
        self.assertTrue(admin.verificarRol(Usuario.TipoRol.ADMINISTRADOR))
        self.assertTrue(admin.verificarRol(Usuario.TipoRol.USUARIO))



class Nota(metaclass=Tabla): ...
class Voz(metaclass=Tabla): ...
class VozDeNota(metaclass=TablaIntermedia):
    tabla_primaria = Nota
    tabla_secundaria = Voz

class Nota(metaclass=Tabla):
    muchosAMuchos = {Voz: VozDeNota}

    def añadirVoz(self, voz):
        self.añadirRelacion(voz, Voz)

    def obtenerVoces(self):
        return self.obtenerMuchos(Voz)

    def borrarVoz(self, voz: Voz):
        self.borrarRelacion(voz, Voz)


class PruebaTablaIntermedia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)

    def test_relacion_entre_nota_y_voces(self):
        notas = Nota.devolverRegistros(self.bdd, cantidad=25, orden={"id": TipoOrden.DESC})
        self.assertGreater(len(notas), 0)

        nota = Nota(self.bdd, id=notas[0].id)
        voces = Voz.devolverRegistros(self.bdd)
        self.assertGreaterEqual(len(voces), 3)

        # Añadir voces
        nota.añadirVoz(voces[0])
        nota.añadirVoz(voces[1])
        nota.añadirVoz(Voz(self.bdd, id=voces[2].id))
        nota.guardar()
        #print(nota)
        self.assertIsNotNone(nota.id)
        obtenidas = nota.obtenerVoces()
        self.assertGreaterEqual(len(obtenidas), 3)

        # Borrar una voz
        for _, voz in obtenidas.items():
            nota.borrarVoz(voz)
            break
        nota.guardar()
        #print(nota)
        self.assertIsNotNone(nota.id)
        nota_recargada = Nota(self.bdd, id=nota.id)
        self.assertIsInstance(nota_recargada, Nota)

class PruebaEscaparParaMySQL(unittest.TestCase):
    """Pruebas unitarias para _escaparParaMySQL."""

    def test_texto_sin_caracteres_especiales(self):
        self.assertEqual(_escaparParaMySQL("hola mundo"), "hola mundo")

    def test_texto_vacio(self):
        self.assertEqual(_escaparParaMySQL(""), "")

    def test_escapa_comilla_simple(self):
        self.assertEqual(_escaparParaMySQL("O'Brien"), "O''Brien")

    def test_escapa_backslash(self):
        self.assertEqual(_escaparParaMySQL("ruta\\archivo"), "ruta\\\\archivo")

    def test_escapa_newline(self):
        self.assertEqual(_escaparParaMySQL("linea1\nlinea2"), "linea1\\nlinea2")

    def test_escapa_carriage_return(self):
        self.assertEqual(_escaparParaMySQL("linea1\rlinea2"), "linea1\\rlinea2")

    def test_elimina_null_byte(self):
        self.assertEqual(_escaparParaMySQL("hola\0mundo"), "holamundo")

    def test_escapa_tab(self):
        self.assertEqual(_escaparParaMySQL("col1\tcol2"), "col1\\tcol2")

    def test_backslash_antes_de_comilla(self):
        """Verifica que backslash se escapa ANTES que comilla simple,
        evitando doble-escape en secuencias como \\'."""
        self.assertEqual(_escaparParaMySQL("\\'"), "\\\\''")

    def test_multiples_caracteres_especiales(self):
        entrada = "O'Brien\\\n\r\0\t"
        resultado = _escaparParaMySQL(entrada)
        self.assertNotIn("\n", resultado)
        self.assertNotIn("\r", resultado)
        self.assertNotIn("\0", resultado)
        self.assertNotIn("\t", resultado)
        self.assertEqual(resultado, "O''Brien\\\\\\n\\r\\t")

    def test_backslash_n_literal_no_se_doble_escapa(self):
        """Un backslash seguido de 'n' (no un newline) debe escapar solo el backslash."""
        self.assertEqual(_escaparParaMySQL("\\n"), "\\\\n")

class PruebaFormatearValorParaSQL(unittest.TestCase):
    """Pruebas unitarias para formatearValorParaSQL con el nuevo escapado."""

    def test_none(self):
        self.assertEqual(formatearValorParaSQL(None), "NULL")

    def test_bool_true(self):
        self.assertEqual(formatearValorParaSQL(True), "1")

    def test_bool_false(self):
        self.assertEqual(formatearValorParaSQL(False), "0")

    def test_entero(self):
        self.assertEqual(formatearValorParaSQL(42), "42")

    def test_flotante(self):
        self.assertEqual(formatearValorParaSQL(3.14), "3.14")

    def test_decimal(self):
        self.assertEqual(formatearValorParaSQL(Decimal("99.99")), "99.99")

    def test_str_simple(self):
        self.assertEqual(formatearValorParaSQL("hola"), "'hola'")

    def test_str_con_comilla(self):
        self.assertEqual(formatearValorParaSQL("O'Brien"), "'O''Brien'")

    def test_str_con_backslash(self):
        self.assertEqual(formatearValorParaSQL("ruta\\archivo"), "'ruta\\\\archivo'")

    def test_str_con_newline(self):
        self.assertEqual(formatearValorParaSQL("linea1\nlinea2"), "'linea1\\nlinea2'")

    def test_str_con_tab(self):
        self.assertEqual(formatearValorParaSQL("col1\tcol2"), "'col1\\tcol2'")

    def test_str_con_carriage_return(self):
        self.assertEqual(formatearValorParaSQL("a\rb"), "'a\\rb'")

    def test_str_con_null_byte(self):
        self.assertEqual(formatearValorParaSQL("a\0b"), "'ab'")

    def test_str_parecido(self):
        resultado = formatearValorParaSQL("buscar", parecido=True)
        self.assertTrue(resultado.startswith("'%"))
        self.assertTrue(resultado.endswith("%'"))

    def test_date(self):
        self.assertEqual(formatearValorParaSQL(date(2025, 1, 15)), "'2025-01-15'")

    def test_datetime(self):
        resultado = formatearValorParaSQL(datetime(2025, 1, 15, 10, 30, 0))
        self.assertEqual(resultado, "'2025-01-15T10:30:00'")

    def test_bytes(self):
        self.assertEqual(formatearValorParaSQL(b'\xde\xad'), "X'dead'")

    def test_dict_con_caracteres_especiales(self):
        resultado = formatearValorParaSQL({"clave": "valor\ncon\nnewlines"})
        self.assertNotIn("\n", resultado[1:-1].replace("\\n", ""))

    def test_str_multiples_especiales(self):
        entrada = "texto\ncon\\todo'\r\0\t"
        resultado = formatearValorParaSQL(entrada)
        self.assertTrue(resultado.startswith("'"))
        self.assertTrue(resultado.endswith("'"))
        interior = resultado[1:-1]
        self.assertNotIn("\n", interior)
        self.assertNotIn("\r", interior)
        self.assertNotIn("\0", interior)
        self.assertNotIn("\t", interior)

class PruebaExtraerTabla(unittest.TestCase):
    """Pruebas unitarias para _extraer_tabla (sin base de datos)."""

    def test_insert_builder(self):
        sql = "INSERT\nINTO Fragmento\nSET Fragmento.hash = 'abc'\n;"
        self.assertEqual(_extraer_tabla(sql), 'Fragmento')

    def test_insert_raw(self):
        self.assertEqual(_extraer_tabla("INSERT INTO Cliente (nombre) VALUES ('Ana')"), 'Cliente')

    def test_replace_into(self):
        self.assertEqual(_extraer_tabla("REPLACE INTO Tabla (id) VALUES (1)"), 'Tabla')

    def test_update_builder(self):
        sql = "UPDATE\nFragmento\nSET Fragmento.refcount = refcount + 1\n;"
        self.assertEqual(_extraer_tabla(sql), 'Fragmento')

    def test_update_raw(self):
        self.assertEqual(_extraer_tabla("UPDATE Cliente SET nombre = 'X' WHERE id = 1"), 'Cliente')

    def test_delete_builder(self):
        sql = "DELETE\nFROM Instantanea\nWHERE Instantanea.id IS NOT NULL\n;"
        self.assertEqual(_extraer_tabla(sql), 'Instantanea')

    def test_delete_raw(self):
        self.assertEqual(_extraer_tabla("DELETE FROM Nota WHERE id = 5"), 'Nota')

    def test_select_builder(self):
        sql = "SELECT\nFragmento.hash, Fragmento.tamano\nFROM Fragmento\nWHERE Fragmento.id IS NOT NULL\n;"
        self.assertEqual(_extraer_tabla(sql), 'Fragmento')

    def test_select_raw(self):
        self.assertEqual(_extraer_tabla("SELECT id, nombre FROM Cliente WHERE id = 1"), 'Cliente')

    def test_truncate(self):
        self.assertEqual(_extraer_tabla("TRUNCATE TABLE EventoAuditoria"), 'EventoAuditoria')

    def test_alter_table(self):
        self.assertEqual(_extraer_tabla("ALTER TABLE Fragmento ADD COLUMN foo INT"), 'Fragmento')

    def test_drop_table(self):
        self.assertEqual(_extraer_tabla("DROP TABLE Foo"), 'Foo')

    def test_drop_table_if_exists(self):
        self.assertEqual(_extraer_tabla("DROP TABLE IF EXISTS Foo"), 'Foo')

    def test_create_table_if_not_exists(self):
        self.assertEqual(_extraer_tabla("CREATE TABLE IF NOT EXISTS Bar (id INT)"), 'Bar')

    def test_sql_vacio(self):
        self.assertIsNone(_extraer_tabla(""))

    def test_verbo_desconocido(self):
        self.assertIsNone(_extraer_tabla("CALL procedimiento()"))


class PruebaConfigurarAuditoria(unittest.TestCase):
    """Pruebas unitarias para configurar_auditoria (sin base de datos)."""

    def setUp(self):
        self._tabla_orig = _auditoria_mod._tabla_auditoria
        self._lecturas_orig = _auditoria_mod._trazar_lecturas

    def tearDown(self):
        _auditoria_mod._tabla_auditoria = self._tabla_orig
        _auditoria_mod._trazar_lecturas = self._lecturas_orig

    def test_desactivado_por_defecto(self):
        _auditoria_mod._tabla_auditoria = None
        self.assertIsNone(_auditoria_mod._tabla_auditoria)

    def test_activa_tabla_default(self):
        configurar_auditoria()
        self.assertEqual(_auditoria_mod._tabla_auditoria, 'EventoAuditoria')

    def test_activa_tabla_personalizada(self):
        configurar_auditoria('MiLog')
        self.assertEqual(_auditoria_mod._tabla_auditoria, 'MiLog')

    def test_trazar_lecturas_default_false(self):
        configurar_auditoria()
        self.assertFalse(_auditoria_mod._trazar_lecturas)

    def test_trazar_lecturas_true(self):
        configurar_auditoria(trazar_lecturas=True)
        self.assertTrue(_auditoria_mod._trazar_lecturas)

    def test_trazar_lecturas_es_kwonly(self):
        with self.assertRaises(TypeError):
            configurar_auditoria('TablaX', True)


class PruebaLastrowidAuditoria(unittest.TestCase):
    """Pruebas unitarias del cache de lastrowid con auditoría."""

    class CursorFalso:
        def __init__(self):
            self.lastrowid = None
            self.consultas = []

        def execute(self, consulta):
            self.consultas.append(consulta)
            self.lastrowid = 900 if 'EventoAuditoria' in consulta else 123

    class ConexionFalsa:
        def commit(self):
            pass

    def setUp(self):
        self._tabla_orig = _auditoria_mod._tabla_auditoria
        self._lecturas_orig = _auditoria_mod._trazar_lecturas
        configurar_auditoria('EventoAuditoria')

    def tearDown(self):
        _auditoria_mod._tabla_auditoria = self._tabla_orig
        _auditoria_mod._trazar_lecturas = self._lecturas_orig

    def _bdd_falsa(self):
        bdd = BaseDeDatos_MySQL()
        cursor = self.CursorFalso()
        setattr(bdd, '_BaseDeDatos_MySQL__cursor', cursor)
        setattr(bdd, '_BaseDeDatos_MySQL__conexion', self.ConexionFalsa())
        return bdd, cursor

    def test_ejecutar_str_preserva_lastrowid_principal(self):
        bdd, cursor = self._bdd_falsa()

        bdd.ejecutar("INSERT INTO RegistroSimple (valor) VALUES ('x')")

        self.assertEqual(cursor.lastrowid, 900)
        self.assertEqual(bdd.devolverIdUltimaInsercion(), 123)

    def test_builder_preserva_lastrowid_principal(self):
        bdd, cursor = self._bdd_falsa()

        bdd.INSERT('RegistroSimple', valor='x').ejecutar()

        self.assertEqual(cursor.lastrowid, 900)
        self.assertEqual(bdd.devolverIdUltimaInsercion(), 123)


class PruebaAuditoria(unittest.TestCase):
    """Pruebas de integración para el hook de auditoría (requiere base de datos)."""

    @classmethod
    def setUpClass(cls):
        cls.bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)

    def setUp(self):
        self._tabla_orig = _auditoria_mod._tabla_auditoria
        self._lecturas_orig = _auditoria_mod._trazar_lecturas
        _auditoria_mod._tabla_auditoria = None  # desactivar durante la limpieza
        with self.bdd:
            self.bdd.ejecutar("DELETE FROM EventoAuditoria")
            self.bdd.ejecutar("DELETE FROM RegistroSimple")
        configurar_auditoria('EventoAuditoria')

    def tearDown(self):
        _auditoria_mod._tabla_auditoria = self._tabla_orig
        _auditoria_mod._trazar_lecturas = self._lecturas_orig

    def _contar_auditorias(self, operacion=None, tabla_objetivo=None):
        conditions = []
        if operacion:
            conditions.append(f"operacion = '{operacion}'")
        if tabla_objetivo:
            conditions.append(f"tabla_objetivo = '{tabla_objetivo}'")
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        conn = mysql.connector.connect(
            host=MYSQL_HOST, user="usuario_de_prueba",
            password="pRU3b4s!1?2@3$4", database="chastack_bdd_pruebas"
        )
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT COUNT(*) as n FROM EventoAuditoria{where}")
            result = cur.fetchone()
            return result['n'] if result else 0
        finally:
            cur.close()
            conn.close()

    def _desfasar_autoincrement_auditoria(self):
        _auditoria_mod._tabla_auditoria = None
        valores = ", ".join(["('semilla', 'INSERT', 'semilla')"] * 5)
        with self.bdd:
            self.bdd.ejecutar(
                "INSERT INTO EventoAuditoria (tabla_objetivo, operacion, consulta) "
                f"VALUES {valores}"
            )
        configurar_auditoria('EventoAuditoria')

    def _id_registro_simple(self, valor):
        conn = mysql.connector.connect(
            host=MYSQL_HOST, user="usuario_de_prueba",
            password="pRU3b4s!1?2@3$4", database="chastack_bdd_pruebas"
        )
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM RegistroSimple WHERE valor = %s", (valor,))
            row = cur.fetchone()
            return row['id'] if row else None
        finally:
            cur.close()
            conn.close()

    def _id_auditoria_para_valor(self, valor):
        conn = mysql.connector.connect(
            host=MYSQL_HOST, user="usuario_de_prueba",
            password="pRU3b4s!1?2@3$4", database="chastack_bdd_pruebas"
        )
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id FROM EventoAuditoria "
                "WHERE tabla_objetivo = 'RegistroSimple' AND consulta LIKE %s "
                "ORDER BY id DESC LIMIT 1",
                (f"%{valor}%",)
            )
            row = cur.fetchone()
            return row['id'] if row else None
        finally:
            cur.close()
            conn.close()

    def test_insert_preserva_lastrowid_de_consulta_principal(self):
        self._desfasar_autoincrement_auditoria()
        valor = f"lastrowid_builder_{datetime.now().isoformat()}"
        with self.bdd:
            id_devuelto = self.bdd.INSERT('RegistroSimple', valor=valor).ejecutar().devolverIdUltimaInsercion()

        id_real = self._id_registro_simple(valor)
        id_auditoria = self._id_auditoria_para_valor(valor)
        self.assertEqual(id_devuelto, id_real)
        self.assertNotEqual(id_devuelto, id_auditoria)

    def test_guardar_preserva_id_de_registro_con_auditoria(self):
        self._desfasar_autoincrement_auditoria()
        valor = f"lastrowid_registro_{datetime.now().isoformat()}"
        registro = RegistroSimple(self.bdd, {'valor': valor})

        id_devuelto = registro.guardar()

        id_real = self._id_registro_simple(valor)
        id_auditoria = self._id_auditoria_para_valor(valor)
        self.assertEqual(id_devuelto, id_real)
        self.assertEqual(registro.id, id_real)
        self.assertNotEqual(id_devuelto, id_auditoria)

    def test_insert_genera_registro(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='test_insert').ejecutar()
        self.assertEqual(self._contar_auditorias('INSERT', 'RegistroSimple'), 1)

    def test_update_genera_registro(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='para_update').ejecutar()
            self.bdd.UPDATE('RegistroSimple', valor='actualizado').WHERE(valor='para_update').ejecutar()
        self.assertEqual(self._contar_auditorias('UPDATE', 'RegistroSimple'), 1)

    def test_delete_genera_registro(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='para_delete').ejecutar()
            self.bdd.DELETE('RegistroSimple').WHERE(valor='para_delete').ejecutar()
        self.assertEqual(self._contar_auditorias('DELETE', 'RegistroSimple'), 1)

    def test_select_no_auditado_por_defecto(self):
        with self.bdd:
            self.bdd.SELECT('RegistroSimple', ['id', 'valor']).ejecutar()
        self.assertEqual(self._contar_auditorias('SELECT', 'RegistroSimple'), 0)

    def test_select_auditado_con_trazar_lecturas(self):
        configurar_auditoria(trazar_lecturas=True)
        with self.bdd:
            self.bdd.SELECT('RegistroSimple', ['id', 'valor']).ejecutar()
        self.assertEqual(self._contar_auditorias('SELECT', 'RegistroSimple'), 1)

    def test_describe_no_auditado(self):
        configurar_auditoria(trazar_lecturas=True)
        with self.bdd:
            self.bdd.DESCRIBE('RegistroSimple').ejecutar()
        self.assertEqual(self._contar_auditorias(), 0)

    def test_sin_configurar_no_audita(self):
        _auditoria_mod._tabla_auditoria = None
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='sin_audit').ejecutar()
        self.assertEqual(self._contar_auditorias(), 0)

    def test_ejecutar_str_genera_registro(self):
        with self.bdd:
            self.bdd.ejecutar("INSERT INTO RegistroSimple (valor) VALUES ('raw_sql')")
        self.assertEqual(self._contar_auditorias('INSERT', 'RegistroSimple'), 1)

    def test_ejecutar_str_update_genera_registro(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='para_raw_update').ejecutar()
            self.bdd.ejecutar("UPDATE RegistroSimple SET valor = 'raw_updated' WHERE valor = 'para_raw_update'")
        self.assertEqual(self._contar_auditorias('UPDATE', 'RegistroSimple'), 1)

    def test_ejecutar_str_delete_genera_registro(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='para_raw_delete').ejecutar()
            self.bdd.ejecutar("DELETE FROM RegistroSimple WHERE valor = 'para_raw_delete'")
        self.assertEqual(self._contar_auditorias('DELETE', 'RegistroSimple'), 1)

    def test_sin_recursion(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='recursion_guard').ejecutar()
        self.assertEqual(self._contar_auditorias('INSERT'), 1)

    def test_registro_contiene_tabla_objetivo_y_operacion(self):
        with self.bdd:
            self.bdd.INSERT('RegistroSimple', valor='contenido').ejecutar()
        conn = mysql.connector.connect(
            host=MYSQL_HOST, user="usuario_de_prueba",
            password="pRU3b4s!1?2@3$4", database="chastack_bdd_pruebas"
        )
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT tabla_objetivo, operacion, consulta FROM EventoAuditoria ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['tabla_objetivo'], 'RegistroSimple')
            self.assertEqual(row['operacion'], 'INSERT')
            self.assertIn('RegistroSimple', row['consulta'])
        finally:
            cur.close()
            conn.close()


class PruebaTransaccion(unittest.TestCase):
    """transaccion(): atomicidad commit/rollback, anidado y lastrowid."""

    @classmethod
    def setUpClass(cls):
        cls.bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)

    def setUp(self):
        # Auditoría desactivada: aquí se prueba la transacción, no la auditoría.
        self._tabla_orig = _auditoria_mod._tabla_auditoria
        _auditoria_mod._tabla_auditoria = None
        with self.bdd:
            self.bdd.ejecutar("DELETE FROM RegistroSimple")

    def tearDown(self):
        _auditoria_mod._tabla_auditoria = self._tabla_orig

    def _contar(self) -> int:
        bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)
        with bdd as c:
            c.SELECT("RegistroSimple", ["id"]).ejecutar()
            filas = c.devolverResultados()
        return len(filas or [])

    def test_commit_persiste_todo(self):
        with self.bdd.transaccion() as c:
            c.INSERT("RegistroSimple", valor="a").ejecutar()
            c.INSERT("RegistroSimple", valor="b").ejecutar()
        self.assertEqual(self._contar(), 2)

    def test_rollback_revierte_todo(self):
        with self.assertRaises(RuntimeError):
            with self.bdd.transaccion() as c:
                c.INSERT("RegistroSimple", valor="x").ejecutar()
                c.INSERT("RegistroSimple", valor="y").ejecutar()
                raise RuntimeError("fallo a mitad de la transacción")
        self.assertEqual(self._contar(), 0)   # ninguno de los dos persiste

    def test_lastrowid_dentro_de_transaccion(self):
        with self.bdd.transaccion() as c:
            c.INSERT("RegistroSimple", valor="z").ejecutar()
            rid = c.devolverIdUltimaInsercion()
        self.assertIsNotNone(rid)
        bdd = BaseDeDatos_MySQL(CONFIG_BDD_PRUEBAS)
        with bdd as c:
            c.SELECT("RegistroSimple", ["id"]).WHERE(valor="z").ejecutar()
            fila = c.devolverUnResultado()
        self.assertEqual(rid, fila["id"])

    def test_anidada_participa_de_la_externa(self):
        # La transacción interna no commitea por su cuenta: un rollback externo
        # revierte también lo escrito dentro de la anidada.
        with self.assertRaises(RuntimeError):
            with self.bdd.transaccion() as c:
                c.INSERT("RegistroSimple", valor="ext").ejecutar()
                with c.transaccion() as c2:
                    c2.INSERT("RegistroSimple", valor="int").ejecutar()
                raise RuntimeError("fallo externo tras la anidada")
        self.assertEqual(self._contar(), 0)

    def test_autocommit_sin_transaccion_intacto(self):
        # Sin transaccion(), cada ejecutar() commitea (comportamiento histórico).
        with self.bdd:
            self.bdd.INSERT("RegistroSimple", valor="auto").ejecutar()
        self.assertEqual(self._contar(), 1)


# REFACTORIZAR: (Hernán) Segregar pruebas en submódulos.
if __name__ == "__main__":
    try:
        crearBaseDeDatos()
        crearYPoblarTablas()
        unittest.main()
    finally:
        destruirBaseDeDatos()
