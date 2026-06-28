"""
===============
chastack-bdd
===============
Módulo de Python 3.x con abstracciones útiles para gestión de Bases de Datos y construcción de modelos.

* Repositorio del proyecto: https://github.com/Hernanatn/bdd.py

Derechos de autor (c) 2025 Ch'aska SRL. Distribuído bajo licencia MIT.
Autores:
 - Hernan ATN | herni@cajadeideas.ar 
 - Joaquín C. | correajoaquin7@gmail.com
"""

from chastack_bdd.tipos import *
from chastack_bdd.errores import *
from chastack_bdd.utiles import *
from chastack_bdd.bdd import *
from chastack_bdd.tabla import *
from chastack_bdd.registro import *
from chastack_bdd.usuario import *
from chastack_bdd.auditoria import configurar_auditoria

if __name__ == '__main__':
    print(__doc__)