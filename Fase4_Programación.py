# Nombre: Julieth Alexandra Benavides Ortiz
# Grupo: 353
# Curso: Programación
# Fase 4 - componente práctico 
# Sistema Integral de Gestión de Clientes, Servicios y Reservas
#--------------------------------importaciones-----------------------------------------------------------------------------------
import logging  # Escritura de logs 
import math     # Para detectar NaN e infinitos 
import re       # Expresiones regulares (validar formatos)
import sys      # salida de errores y configuracion de la consola
from abc import ABC, abstractmethod # Clases y metodos abstractos
from collections import Counter     # Conteo de reservas por estados
from datetime import datetime       # Fecha de creación de las entidades
from enum import Enum               # Enumeración de estados de reserva
from pathlib import Path            # Rutas de archivos portables
#======================================================================================================================
