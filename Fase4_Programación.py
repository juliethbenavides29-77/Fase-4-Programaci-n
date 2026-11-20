# Nombre: Julieth Alexandra Benavides Ortiz 
# Nombre: Luis Eduardo Vidal Hinestroza
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
#======================================================================================================================
# EXCEPCIONES PERSONALIZADAS
#=======================================================================================================================
class ErrorSoftwareFJ(Exception):
    # Excepción base de todo el sistema. Nunca se usa sola, se hereda de ella.
    # Codigo corto que identifica el tipo de error 
    CODIGO = "SFJ-000"
    # Mensaje que se usa si quien lanza la excepción no escribe uno 
    MENSAJE_POR_DEFECTO = "Error general en el sistema Software FJ"

    def __init__(self, mensaje=None):
        # si no llega mensaje (o llega vacio) se usa el mensaje por defecto.
        self.mensaje = mensaje or self.MENSAJE_POR_DEFECTO
        # se llama al constructor  de Excepción para que el mensaje quede guardado
        super().__init__(self.mensaje)

    def __str__(self):
        # al imprimir la excepción se muestra: [CODIGO] mensaje
        return f"[{self.CODIGO}] {self.mensaje}"

class ErrorValidacion(ErrorSoftwareFJ):
    # Error generico de validación de datos (agrupa los errores de datos inválidos).
    CODIGO = "SFJ-100"
    MENSAJE_POR_DEFECTO = "Los datos suministrados no son válidos."

class ClienteInvalidoError(ErrorValidacion):
    # se lanza cuando los datos personales de un cliente no cumplen las reglas.

    CODIGO = "SFJ-101"
    MENSAJE_POR_DEFECTO = "Los datos del cliente no son válidos."

class ServicioInvalidoError(ErrorValidacion):
    # se lanza cuando los parámetros de un servicio (o su duración) son inválidos.

    CODIGO = "SFJ-102"
    MENSAJE_POR_DEFECTO = "Los parámetros del servicio no son válidos."

class ParametroFaltanteError(ErrorValidacion):
    # se lanza cuando falta un dato obligatorio (None o texto vacio).

    CODIGO = "SFJ-103"
    MENSAJE_POR_DEFECTO = "Falta uno o más parámetros obligatorios."

class ServicioNoDisponibleError(ErrorSoftwareFJ):
    # se lanza cuando se intenta usar un servicio que está marcado como no disponible

    CODIGO = "SFJ-200"
    MENSAJE_POR_DEFECTO = "El servicio solicitado no está disponible."

class OperacionNoPermitidaError(ErrorSoftwareFJ):
    # se lanza cuando se pide una operación que el estado actual no permite 

    CODIGO = "SFJ-300"
    MENSAJE_POR_DEFECTO = "La operación solicitada no está permitida."

class ReservaInvalidaError(ErrorSoftwareFJ):
    # se lanza cuando un intento de reserva es incorrecto (cliente o servicio inexistente, duración fuera de rango, etc.).
    
    CODIGO = "SFJ-400"
    MENSAJE_POR_DEFECTO = "El intento de reserva es incorrecto."

class CalculoInconsistenteError(ErrorSoftwareFJ):
    # se lanza cuando un cálculo de costos produce o recibe valores absurdos (impuestos negativos, descuentos mayores al 100%, Nan, costos menores o igual a 0)
    
    CODIGO = "SFJ-500"
    MENSAJE_POR_DEFECTO = "El cálculo de costos es inconsistente."

#==========================================================================================================================================================
# SISTEMA DE LOGS
#=============================================================================================================================================
# Manejo de archivos únicamente para el registro de eventos y errores
# Carpeta donde se guardará el log: <carpeta del proyecto>/logs
RUTA_LOGS = Path(__file__).resolve().parent / "logs"
# Ruta completa del archivo de log
ARCHIVO_LOG = RUTA_LOGS / "software_fj.log"

def _configurar_logger():
    # crea una sola vez y devuelve el logger del sistema.
    # `getLogger`con el mismo nombre siempre devuelve el mismo objeto.
    logger = logging.getLogger("software_fj")

    # si ya tiene manejandores, ya fue configurado: se utiliza tal cual
    if logger.handlers:
        return logger

    # se registran mensajes desde nivel INFO hacia arriba (INFO, WARNING, ERROR).
    logger.setLevel(logging.INFO)
    # evita que los mensajes suban al logger raiz y se impriman duplicados
    logger.propagate = False

    try:
        # se crea la carpeta de logs (exist_ok evita error si ya existe)
        RUTA_LOGS.mkdir(parents=True, exist_ok=True)
        # manejador que escribe en el archivo (modo "a"= agregar al final)
        manejador = logging.FileHandler(ARCHIVO_LOG, mode="a", encoding="utf-8")
    except OSError as error:
        # respaldo: si no se puede escribir el archivo, se usa la pantalla.
        print(f"[AVISO] No se pudo abrir el archivo de logs ({error})." f"Se usará la pantalla.",file=sys.stderr) 
        manejador = logging.StreamHandler(sys.stderr)

        #formato de cada linea: fecha y hora/ nivel/ mensaje
    formato = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    manejador.setFormatter(formato) # se asocia el formato al manejador
    logger.addHandler(manejador)    # se asocia el manejador al logger
    return logger

# logger global del módulo (se crea al importar el archivo).
_logger = _configurar_logger()

def _describir_cadena(excepcion):
    # devuelve un texto con la cadena de excepciones (causa -> consecuencia).
    partes = []        # aqui se acumula cada eslabon de la cadena
    vistas = set()     # Ids ya visitados (evita bucles infinitos)
    actual = excepcion # Eslabón que se está procesando

    while actual is not None and id(actual) not in vistas:
        vistas.add(id(actual)) #se marca como visitado
        partes.append(f"{type(actual).__name__}: {actual}")
        # se avanza a la causa explicita; si no hay, al contexto implicito.
        actual = actual.__cause__ or actual.__context__
    # se unen los eslabones con una flecha para leerlos facilmente.
    return "<-causado por-  ".join(partes)

def registrar_evento(mensaje):
    #registra un evento normal del sistema (nivel INFO).
    _logger.info(mensaje)

def registrar_advertencia(mensaje):
    #registra una advertencia (nivel WARNING).
    _logger.warning(mensaje)

def registrar_error(mensaje, excepcion=None):
    # registra un error (nivel ERROR). Si se pasa la excepción, tambien se escribe toda su cadena de causas en el log.
    if excepcion is not None:
        # se añade al mensaje la cadena completa de excepciones
        mensaje = f"{mensaje} || {_describir_cadena(excepcion)}"
    _logger.error(mensaje)

#======================================================================================================================================================================
# CLASE ABSTRACTA BASE: EntidadBase
#======================================================================================================================================================================
# represente entidades generales del sistema
# Cliente, Servicio y Reserva heredan de EntidadBase. Todas comparten:
# Un identificador único autogenerado,
# Una fecha de creación,
# la obligación de implementar describir() (método abstracto)
def formato_cop(valor):
    """Da formato de pesos colombianos a un número. Ej.: 1234567.5 -> $1,234,568"""
    return f"${valor:,.0f}"


class EntidadBase(ABC):
    # Clase abstracta: NO se puede instanciar directamente (EntidadBase())

    # Atributo de CLASE (compartido por todas las entidades): diccionario que lleva la cuenta de identificadores entregados por cada FAMILIA de entidad
    # (así hay Cliente #1, Servicio #1 y Reserva #1, cada uno con su propia numeración)
    _contadores_ids = {}

    # Nombre de la familia de ids. Cada clase principal lo redefine
    # (Cliente -> "cliente", Servicio -> "servicio", Reserva -> "reserva").
    FAMILIA_ID = "entidad"

    def __init__(self):
        # Se incrementa el contador de la familia de esta entidad
        familia = self.FAMILIA_ID
        EntidadBase._contadores_ids[familia] = EntidadBase._contadores_ids.get(familia, 0) + 1
        # y se guarda como id de esta entidad (atributo protegido con "_").
        self._id = EntidadBase._contadores_ids[familia]
        # Momento exacto en que se creó la entidad.
        self._fecha_creacion = datetime.now()

    # ---- Propiedades de solo lectura (encapsulación) -------------------------
    @property
    def id(self):
        """Identificador único (no tiene setter: nadie puede modificarlo)."""
        return self._id

    @property
    def fecha_creacion(self):
        """Fecha y hora de creación (solo lectura)."""
        return self._fecha_creacion

    # ---- Método abstracto: obliga a las hijas a implementarlo ----------------
    @abstractmethod
    def describir(self):
        """Devuelve un texto que describe la entidad. Cada hija lo implementa a
        su manera (esto es POLIMORFISMO: mismo método, distinto comportamiento)."""

    def __str__(self):
        # Al hacer print(entidad) se muestra su descripción.
        return self.describir()

#===========================================================================================================================================================================
# CLASE CLIENTE
#=====================================================================================================================================================================================
# clase Cliente con validaciones robustas y encapsulación de datos personales
class Cliente(EntidadBase):
    # Cliente de Software FJ. Hereda de EntidadBase (id y fecha de creación).

    # Familia de numeración de ids: Cliente #1, Cliente #2, 
    FAMILIA_ID = "cliente"

    # Patrones de validación (atributos de clase, compartidos por todos).
    # Nombre: solo letras (con tildes/ñ), espacios y apóstrofe; 3 a 60 caracteres.
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' ]{3,60}$")
    # Correo: formato general usuario@dominio.ext
    _PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    # Teléfono celular colombiano: 10 dígitos que empiezan por 3.
    _PATRON_TELEFONO = re.compile(r"^3\d{9}$")
    # Documento: solo dígitos, entre 6 y 12.
    _PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")

    def __init__(self, nombre=None, documento=None, correo=None, telefono=None):
        # ---  Parámetros faltantes -------------------------------------------
        # Se arma un diccionario con los datos recibidos para revisarlos juntos.
        recibidos = {"nombre": nombre, "documento": documento,
                     "correo": correo, "telefono": telefono}
        # Un dato "falta" si es None o si es un texto vacío / solo espacios.
        faltantes = [campo for campo, valor in recibidos.items()
                     if valor is None or (isinstance(valor, str) and not valor.strip())]
        if faltantes:
            # Se lanza la excepción personalizada indicando qué campos faltan.
            raise ParametroFaltanteError(
                f"Faltan datos obligatorios del cliente: {', '.join(faltantes)}.")

        # --- Validación de cada dato (try/except con ENCADENAMIENTO) --------
        try:
            # Cada asignación pasa por el setter correspondiente, que valida.
            self.nombre = nombre
            self.documento = documento
            self.correo = correo
            self.telefono = telefono
        except ClienteInvalidoError as error_original:
            # ENCADENAMIENTO: se lanza un error más general ("no se pudo crear
            # el cliente") conservando el original con `from error_original`.
            raise ClienteInvalidoError(
                f"No se pudo crear el cliente: {error_original.mensaje}"
            ) from error_original

        # --- Lista interna: historial de reservas (ids) ---------------------
        self.__historial_reservas = []

        # ---  Solo si todo fue válido se genera el id de la entidad ----------
        super().__init__()
        registrar_evento(f"Cliente creado: id={self.id}, nombre={self.nombre}")

    # ======================= Propiedades con validación ========================
    @property
    def nombre(self):
        """Nombre del cliente (lectura)."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        """Nombre del cliente (escritura validada)."""
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El nombre debe ser un texto.")
        # " ".join(split()) elimina espacios repetidos o al inicio/final.
        limpio = " ".join(valor.split())
        if not self._PATRON_NOMBRE.match(limpio):
            raise ClienteInvalidoError(
                "El nombre solo puede tener letras y espacios (3 a 60 caracteres).")
        # .title() deja cada palabra con mayúscula inicial.
        self.__nombre = limpio.title()

    @property
    def documento(self):
        """Número de documento (lectura)."""
        return self.__documento

    @documento.setter
    def documento(self, valor):
        """Número de documento (escritura validada)."""
        # bool es subclase de int en Python; se rechaza explícitamente.
        if isinstance(valor, bool) or not isinstance(valor, (int, str)):
            raise ClienteInvalidoError("El documento debe ser un número o un texto numérico.")
        texto = str(valor).strip()          # Se trabaja siempre como texto
        if not self._PATRON_DOCUMENTO.match(texto):
            raise ClienteInvalidoError("El documento debe tener entre 6 y 12 dígitos.")
        self.__documento = texto

    @property
    def correo(self):
        """Correo electrónico (lectura)."""
        return self.__correo

    @correo.setter
    def correo(self, valor):
        """Correo electrónico (escritura validada)."""
        if not isinstance(valor, str) or not self._PATRON_CORREO.match(valor.strip()):
            raise ClienteInvalidoError("El correo electrónico no tiene un formato válido.")
        self.__correo = valor.strip().lower()

    @property
    def telefono(self):
        """Teléfono (lectura)."""
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        """Teléfono (escritura validada)."""
        texto = str(valor).strip() if valor is not None else ""
        if not self._PATRON_TELEFONO.match(texto):
            raise ClienteInvalidoError(
                "El teléfono debe ser un celular colombiano de 10 dígitos (inicia en 3).")
        self.__telefono = texto

    # ======================= Historial (lista interna) =========================
    @property
    def historial_reservas(self):
        """Devuelve una COPIA inmutable (tupla) del historial: la lista interna
        no se puede modificar desde fuera (encapsulación)."""
        return tuple(self.__historial_reservas)

    def agregar_al_historial(self, id_reserva):
        """Agrega el id de una reserva al historial del cliente."""
        self.__historial_reservas.append(id_reserva)

    # ======================= Protección de datos personales ====================
    def documento_enmascarado(self):
        """Devuelve el documento ocultando todo salvo los 3 últimos dígitos."""
        return "*" * (len(self.__documento) - 3) + self.__documento[-3:]

    # ======================= Método abstracto implementado =====================
    def describir(self):
        """Descripción pública del cliente (sin exponer el documento completo)."""
        return (f"Cliente #{self.id} | {self.nombre} | Doc: {self.documento_enmascarado()} "
                f"| {self.correo} | Reservas: {len(self.__historial_reservas)}")
#================================================================================================================================================================================
# CLASE SERVICIOS
#==========================================================================================================================================================================================
# clase abstracta Servicio y tres servicios especializados que hereden de ella" -> ReservaSala, AlquilerEquipo, AsesoriaEspecializada
# implementando polimorfismo y métodos sobrescritos para calcular costos, describir servicios y validar parámetros
class Servicio(EntidadBase):
    # Clase abstracta que define lo común a todos los servicios de Software FJ. Como hereda de EntidadBase (que es abstracta) y deja métodos abstractos sin implementar, tampoco se puede instanciar: Servicio(...) lanza TypeError.
    # Familia de numeración de ids: todos los servicios (sala, equipo, asesoría)
    # comparten la misma numeración: Servicio #1, #2, #3...
    FAMILIA_ID = "servicio"

    # Tipo de servicio y unidad de duración: cada hija los redefine.
    TIPO = "Servicio genérico"
    UNIDAD_DURACION = "unidades"

    # Límites permitidos para impuestos y descuentos (porcentaje en forma decimal).
    IMPUESTO_MAXIMO = 0.30      # Máximo 30 % de impuesto
    DESCUENTO_MAXIMO = 0.50     # Máximo 50 % de descuento

    def __init__(self, nombre=None, tarifa_base=None, disponible=True):
        # --- Parámetros faltantes ---------------------------------------------
        if nombre is None or tarifa_base is None:
            raise ParametroFaltanteError("El servicio requiere 'nombre' y una tarifa.")

        # --- Validación del nombre --------------------------------------------
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ServicioInvalidoError("El nombre del servicio debe tener al menos 3 caracteres.")

        # --- Validación de la tarifa (con ENCADENAMIENTO de excepciones) -------
        try:
            # bool es int en Python (True == 1), por eso se rechaza aparte.
            if isinstance(tarifa_base, bool):
                raise TypeError("la tarifa no puede ser un booleano")
            tarifa = float(tarifa_base)          # Puede lanzar ValueError / TypeError
        except (TypeError, ValueError) as error_original:
            # Se envuelve el error técnico en uno del dominio, conservando la causa.
            raise ServicioInvalidoError(
                f"La tarifa '{tarifa_base}' no es un número válido.") from error_original
        if not math.isfinite(tarifa) or tarifa <= 0:
            raise ServicioInvalidoError("La tarifa debe ser un número mayor que cero.")

        # --- Todo válido: se genera el id y se guardan los atributos ----------
        super().__init__()
        self._nombre = nombre.strip()            # Atributos protegidos (un guion bajo)
        self._tarifa_base = tarifa
        self._disponible = bool(disponible)
        registrar_evento(f"Servicio creado: id={self.id}, tipo={self.TIPO}, nombre={self._nombre}")

    # ----------------------------- Propiedades --------------------------------
    @property
    def nombre(self):
        """Nombre del servicio (solo lectura)."""
        return self._nombre

    @property
    def tarifa_base(self):
        """Tarifa base del servicio (solo lectura)."""
        return self._tarifa_base

    @property
    def disponible(self):
        """Indica si el servicio se puede reservar."""
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        """Permite activar/desactivar el servicio y deja constancia en el log."""
        self._disponible = bool(valor)
        registrar_evento(f"Servicio #{self.id} '{self.nombre}' -> "
                         f"{'disponible' if self._disponible else 'NO disponible'}")

    # ------------------------- Métodos concretos ------------------------------
    def verificar_disponibilidad(self):
        """Lanza ServicioNoDisponibleError si el servicio no se puede usar."""
        if not self._disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self.nombre}' no está disponible.")

    def _validar_duracion(self, duracion, minimo, maximo, entero=False):
        """Utilidad compartida por las hijas: valida que la duración sea un número
        dentro de [minimo, maximo] y (opcionalmente) entero. Devuelve el valor limpio."""
        try:
            if duracion is None or isinstance(duracion, bool):
                raise TypeError("la duración no puede ser nula ni booleana")
            valor = float(duracion)
        except (TypeError, ValueError) as error_original:
            raise ServicioInvalidoError(
                f"La duración '{duracion}' no es un número válido.") from error_original
        if not math.isfinite(valor):
            raise ServicioInvalidoError("La duración debe ser un número finito.")
        if not (minimo <= valor <= maximo):
            raise ServicioInvalidoError(
                f"La duración debe estar entre {minimo} y {maximo} {self.UNIDAD_DURACION}.")
        if entero:
            if valor != int(valor):
                raise ServicioInvalidoError(
                    f"La duración debe ser un número entero de {self.UNIDAD_DURACION}.")
            return int(valor)
        # Si el valor es "redondo" (3.0) se devuelve como entero (3) para mostrarlo mejor.
        return int(valor) if valor == int(valor) else valor

    # ----------------- MÉTODOS ABSTRACTOS (las hijas DEBEN implementarlos) ----
    @abstractmethod
    def validar_parametros(self, duracion):
        """Valida la duración solicitada según las reglas del servicio y la
        devuelve ya normalizada. Lanza ServicioInvalidoError si no es válida."""

    @abstractmethod
    def calcular_costo_base(self, duracion):
        """Calcula el costo SIN impuestos ni descuentos para una duración ya validada."""

    # describir() también es abstracto: viene declarado en EntidadBase.

    # ------------------- MÉTODO SOBRECARGADO: calcular_costo ------------------
    def calcular_costo(self, duracion, *args, **kwargs):
        """Calcula el costo total con distintas variantes (SOBRECARGA simulada).

        Variantes admitidas (impuesto y descuento son fracciones: 0.19 = 19 %):
            calcular_costo(duracion)
            calcular_costo(duracion, impuesto)
            calcular_costo(duracion, impuesto, descuento)
            calcular_costo(duracion, impuesto=0.19)
            calcular_costo(duracion, descuento=0.10)
            calcular_costo(duracion, impuesto=0.19, descuento=0.10)
        """
        # ---  Resolver qué variante se está usando --------------------------
        nombres = ("impuesto", "descuento")          # Orden de los parámetros posicionales
        if len(args) > len(nombres):
            raise ServicioInvalidoError(
                "calcular_costo admite como máximo: duracion, impuesto y descuento.")
        # Los posicionales se asocian a su nombre según el orden (impuesto, descuento).
        valores = dict(zip(nombres, args))
        for clave, valor in kwargs.items():
            if clave not in nombres:
                raise ServicioInvalidoError(f"Parámetro desconocido en calcular_costo: '{clave}'.")
            if clave in valores:
                raise ServicioInvalidoError(f"El parámetro '{clave}' se indicó dos veces.")
            valores[clave] = valor
        # Lo que no se indicó vale 0 (sin impuesto / sin descuento).
        impuesto = self._convertir_tasa(valores.get("impuesto", 0.0), "impuesto",
                                        self.IMPUESTO_MAXIMO)
        descuento = self._convertir_tasa(valores.get("descuento", 0.0), "descuento",
                                         self.DESCUENTO_MAXIMO)

        # --- Validar la duración con las reglas propias de cada servicio ----
        duracion_valida = self.validar_parametros(duracion)       # POLIMORFISMO

        # --- Costo base (cada servicio lo calcula distinto) -----------------
        base = self.calcular_costo_base(duracion_valida)          # POLIMORFISMO
        if not math.isfinite(base) or base <= 0:
            raise CalculoInconsistenteError(f"El costo base calculado es inválido: {base}.")

        # --- Aplicar descuento y luego impuesto -----------------------------
        subtotal = base * (1 - descuento)       # Primero se descuenta...
        total = subtotal * (1 + impuesto)       # ...y sobre lo descontado se agrega el impuesto
        if not math.isfinite(total) or total <= 0:
            raise CalculoInconsistenteError(f"El costo total calculado es inválido: {total}.")
        return round(total, 2)

    def _convertir_tasa(self, valor, nombre, maximo):
        """Convierte un impuesto/descuento a float y verifica que esté en [0, maximo]."""
        try:
            if isinstance(valor, bool):
                raise TypeError("no puede ser booleano")
            tasa = float(valor)
        except (TypeError, ValueError) as error_original:
            raise CalculoInconsistenteError(
                f"El {nombre} '{valor}' no es un número válido.") from error_original
        if not math.isfinite(tasa) or tasa < 0 or tasa > maximo:
            raise CalculoInconsistenteError(
                f"El {nombre} debe estar entre 0 y {maximo} (recibido: {valor}).")
        return tasa
#===============================================================================================================================================================================================
# =============================================================================
#                      SERVICIO ESPECIALIZADO 1: RESERVA DE SALA
# =============================================================================
class ReservaSala(Servicio):
    """Reserva de salas de reuniones. La duración se mide en HORAS (1 a 12)."""

    TIPO = "Reserva de sala"
    UNIDAD_DURACION = "horas"
    COSTO_PROYECTOR = 20000       # Cargo fijo si la sala incluye proyector

    def __init__(self, nombre=None, capacidad=None, tarifa_hora=None,
                 disponible=True, incluye_proyector=False):
        # Se valida lo propio de la sala ANTES de llamar al constructor del padre.
        if capacidad is None:
            raise ParametroFaltanteError("La sala requiere 'capacidad'.")
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or not (1 <= capacidad <= 200):
            raise ServicioInvalidoError("La capacidad debe ser un entero entre 1 y 200 personas.")
        # super().__init__ valida nombre y tarifa (la tarifa por hora es la base).
        super().__init__(nombre, tarifa_hora, disponible)
        self._capacidad = capacidad
        self._incluye_proyector = bool(incluye_proyector)

    @property
    def capacidad(self):
        """Capacidad máxima de personas (solo lectura)."""
        return self._capacidad

    # --- Métodos SOBRESCRITOS (polimorfismo) ---
    def validar_parametros(self, duracion):
        """Horas de 1 a 12 (se permiten medias horas, ej. 2.5)."""
        return self._validar_duracion(duracion, 1, 12)

    def calcular_costo_base(self, duracion):
        """Tarifa por hora x horas, más el cargo fijo del proyector si aplica."""
        costo = self._tarifa_base * duracion
        if self._incluye_proyector:
            costo += self.COSTO_PROYECTOR
        return costo

    def describir(self):
        """Descripción de la sala."""
        proyector = "con proyector" if self._incluye_proyector else "sin proyector"
        estado = "disponible" if self.disponible else "NO disponible"
        return (f"[{self.TIPO}] #{self.id} {self.nombre} | capacidad {self._capacidad} personas "
                f"| {proyector} | {formato_cop(self._tarifa_base)}/hora | {estado}")


# =============================================================================
#                    SERVICIO ESPECIALIZADO 2: ALQUILER DE EQUIPOS
# =============================================================================
class AlquilerEquipo(Servicio):
    """Alquiler de equipos tecnológicos. La duración se mide en DÍAS (1 a 30, enteros)."""

    TIPO = "Alquiler de equipo"
    UNIDAD_DURACION = "días"
    RECARGO_SEGURO = 0.05         # 5 % extra si se contrata seguro

    def __init__(self, nombre=None, tipo_equipo=None, tarifa_dia=None,
                 unidades=1, disponible=True, seguro=False):
        # Validaciones propias del alquiler.
        if tipo_equipo is None or not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise ParametroFaltanteError("El alquiler requiere 'tipo_equipo' (texto).")
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades < 1:
            raise ServicioInvalidoError("Las unidades deben ser un entero mayor o igual a 1.")
        # La tarifa por día es la tarifa base del servicio.
        super().__init__(nombre, tarifa_dia, disponible)
        self._tipo_equipo = tipo_equipo.strip()
        self._unidades = unidades
        self._seguro = bool(seguro)

    # --- Métodos SOBRESCRITOS (polimorfismo) ---
    def validar_parametros(self, duracion):
        """Días enteros de 1 a 30."""
        return self._validar_duracion(duracion, 1, 30, entero=True)

    def calcular_costo_base(self, duracion):
        """Tarifa por día x días x unidades, más 5 % si incluye seguro."""
        costo = self._tarifa_base * duracion * self._unidades
        if self._seguro:
            costo *= (1 + self.RECARGO_SEGURO)
        return costo

    def describir(self):
        """Descripción del alquiler."""
        seguro = "con seguro" if self._seguro else "sin seguro"
        estado = "disponible" if self.disponible else "NO disponible"
        return (f"[{self.TIPO}] #{self.id} {self.nombre} | {self._tipo_equipo} x{self._unidades} "
                f"| {seguro} | {formato_cop(self._tarifa_base)}/día | {estado}")


# =============================================================================
#                SERVICIO ESPECIALIZADO 3: ASESORÍA ESPECIALIZADA
# =============================================================================
class AsesoriaEspecializada(Servicio):
    """Asesorías con especialistas. La duración se mide en HORAS (1 a 8).
    El nivel del asesor multiplica la tarifa."""

    TIPO = "Asesoría especializada"
    UNIDAD_DURACION = "horas"
    # Multiplicador de tarifa según el nivel del asesor.
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre=None, especialidad=None, tarifa_hora=None,
                 nivel="senior", disponible=True):
        if especialidad is None or not isinstance(especialidad, str) or not especialidad.strip():
            raise ParametroFaltanteError("La asesoría requiere 'especialidad' (texto).")
        # El nivel se normaliza a minúsculas para comparar sin importar cómo se escriba.
        nivel_limpio = str(nivel).strip().lower()
        if nivel_limpio not in self.NIVELES:
            raise ServicioInvalidoError(
                f"Nivel '{nivel}' inválido. Opciones: {', '.join(self.NIVELES)}.")
        super().__init__(nombre, tarifa_hora, disponible)
        self._especialidad = especialidad.strip()
        self._nivel = nivel_limpio

    # --- Métodos SOBRESCRITOS (polimorfismo) ---
    def validar_parametros(self, duracion):
        """Horas de 1 a 8 (se permiten medias horas)."""
        return self._validar_duracion(duracion, 1, 8)

    def calcular_costo_base(self, duracion):
        """Tarifa por hora x horas x multiplicador del nivel del asesor."""
        return self._tarifa_base * duracion * self.NIVELES[self._nivel]

    def describir(self):
        """Descripción de la asesoría."""
        estado = "disponible" if self.disponible else "NO disponible"
        return (f"[{self.TIPO}] #{self.id} {self.nombre} | {self._especialidad} "
                f"| nivel {self._nivel} | {formato_cop(self._tarifa_base)}/hora base | {estado}")
#======================================================================================================================
# IMPORTACIONES
#======================================================================================================================
# Clases y funciones del núcleo que se usan en esta etapa.
from software_fj_core import (
    Cliente,
    Servicio,
    ReservaSala,
    AlquilerEquipo,
    AsesoriaEspecializada,
    EntidadBase,
    ErrorSoftwareFJ,
    ParametroFaltanteError,
    ServicioInvalidoError,
    ReservaInvalidaError,
    OperacionNoPermitidaError,
    formato_cop,
    registrar_evento,
    registrar_error,
)
#======================================================================================================================


#======================================================================================================================
# ESTADOS DE UNA RESERVA
#======================================================================================================================
class EstadoReserva(Enum):
    """Estados por los que pasa una reserva durante su ciclo de vida."""

    # Reserva creada, pero aun no se ha confirmado ni calculado su costo.
    PENDIENTE = "Pendiente"
    # El servicio estaba disponible, se calculó el costo y la reserva quedó confirmada.
    CONFIRMADA = "Confirmada"
    # La reserva se canceló antes de ser procesada.
    CANCELADA = "Cancelada"
    # El servicio ya fue prestado; este es el estado final de una reserva exitosa.
    PROCESADA = "Procesada"
#======================================================================================================================


#======================================================================================================================
# CLASE RESERVA
#======================================================================================================================
class Reserva(EntidadBase):
    """Une un cliente con un servicio durante una duración determinada.

    La reserva no hereda de Cliente ni de Servicio: los contiene (composición).
    De EntidadBase hereda el id automático, la fecha de creación y la obligación
    de implementar describir().
    """

    # Familia de numeración de ids: Reserva #1, Reserva #2, ...
    FAMILIA_ID = "reserva"

    def __init__(self, cliente=None, servicio=None, duracion=None):
        # --- 1. Parámetros faltantes -----------------------------------------
        # None indica que el dato no fue suministrado por quien crea la reserva.
        faltantes = []
        if cliente is None:
            faltantes.append("cliente")
        if servicio is None:
            faltantes.append("servicio")
        if duracion is None:
            faltantes.append("duración")
        if faltantes:
            # Se informa exactamente qué datos hacen falta.
            raise ParametroFaltanteError(
                f"Faltan datos obligatorios de la reserva: {', '.join(faltantes)}.")

        # --- 2. Validación de tipos -------------------------------------------
        # Una reserva solo puede unir objetos reales del dominio del sistema.
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("El cliente debe ser una instancia de Cliente.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("El servicio debe ser una instancia de Servicio.")

        # --- 3. Validación de la duración (POLIMORFISMO) ----------------------
        # Cada servicio decide qué duraciones acepta (horas, días, rangos, etc.).
        # La reserva delega esa regla en el servicio correspondiente.
        try:
            duracion_valida = servicio.validar_parametros(duracion)
        except (ServicioInvalidoError, ParametroFaltanteError) as error_original:
            # ENCADENAMIENTO: se conserva el error original como causa del nuevo.
            raise ReservaInvalidaError(
                f"No se pudo crear la reserva: {error_original.mensaje}"
            ) from error_original

        # --- 4. Atributos internos (encapsulación) ----------------------------
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion_valida
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None

        # --- 5. Id y fecha de creación ----------------------------------------
        # Se llama al final para que una reserva inválida no consuma un id.
        super().__init__()

        # --- 6. Registro del evento -------------------------------------------
        registrar_evento(
            f"Reserva creada: id={self.id}, cliente={cliente.nombre}, "
            f"servicio={servicio.nombre}, duración={duracion_valida} "
            f"{servicio.UNIDAD_DURACION}"
        )

    # ======================= Propiedades de solo lectura =======================
    @property
    def cliente(self):
        """Cliente asociado a la reserva (solo lectura)."""
        return self._cliente

    @property
    def servicio(self):
        """Servicio asociado a la reserva (solo lectura)."""
        return self._servicio

    @property
    def duracion(self):
        """Duración ya validada y normalizada (solo lectura)."""
        return self._duracion

    @property
    def estado(self):
        """Estado actual de la reserva (solo lectura)."""
        return self._estado

    @property
    def costo_total(self):
        """Costo calculado al confirmar; None mientras no se confirme."""
        return self._costo_total

    # ======================= Ciclo de vida de la reserva =======================
    def confirmar(self, impuesto=0.0, descuento=0.0):
        """Confirma la reserva, verifica disponibilidad y calcula el costo total."""
        # Solo se puede confirmar una reserva que todavía está pendiente.
        if self._estado != EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva en estado {self._estado.value}."
            )

        # El servicio debe estar disponible en el momento de confirmar.
        # Si no lo está, se lanza ServicioNoDisponibleError.
        self._servicio.verificar_disponibilidad()

        # Se calcula el costo usando la variante sobrecargada del servicio.
        # Puede lanzar CalculoInconsistenteError si el impuesto o el descuento
        # están fuera de los límites permitidos.
        costo = self._servicio.calcular_costo(
            self._duracion, impuesto=impuesto, descuento=descuento
        )

        # Solo si todo salió bien se actualiza el estado y el costo.
        self._costo_total = costo
        self._estado = EstadoReserva.CONFIRMADA
        self._cliente.agregar_al_historial(self.id)

        registrar_evento(
            f"Reserva #{self.id} confirmada: cliente={self._cliente.nombre}, "
            f"servicio={self._servicio.nombre}, total={formato_cop(costo)}"
        )
        return costo

    def cancelar(self):
        """Cancela una reserva pendiente o confirmada."""
        # Una reserva ya cancelada o procesada no se puede cancelar de nuevo.
        if self._estado not in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva en estado {self._estado.value}."
            )

        self._estado = EstadoReserva.CANCELADA
        registrar_evento(f"Reserva #{self.id} cancelada.")

    def procesar(self):
        """Marca como procesada una reserva que ya fue confirmada."""
        # Solo una reserva confirmada puede pasar al estado procesada.
        if self._estado != EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"No se puede procesar una reserva en estado {self._estado.value}."
            )

        self._estado = EstadoReserva.PROCESADA
        registrar_evento(f"Reserva #{self.id} procesada.")

    # ======================= Se implementa el método abstracto describir() =====================
    def describir(self):
        """Devuelve un texto con los datos principales de la reserva."""
        # Mientras la reserva no se confirme, el costo todavía no existe.
        if self._costo_total is None:
            costo = "falta calcular"
        else:
            costo = formato_cop(self._costo_total)
        return (
            f"Reserva #{self.id} | Cliente: {self._cliente.nombre} "
            f"| Servicio: {self._servicio.nombre} "
            f"| Duración: {self._duracion} {self._servicio.UNIDAD_DURACION} "
            f"| Estado: {self._estado.value} | Costo: {costo}"
        )
#======================================================================================================================


#======================================================================================================================
# FUNCION AUXILIAR PARA LA SIMULACIÓN
#======================================================================================================================
def ejecutar_operacion(numero, descripcion, accion, *args, **kwargs):
    """Ejecuta una operación de la simulación y controla sus errores.

    Recibe la acción y los argumentos que necesita. Se usa
    try/except/else/finally para demostrar el manejo completo:
    - try: intenta ejecutar la operación.
    - except: captura errores del dominio o errores inesperados.
    - else: se ejecuta solo si no hubo error.
    - finally: se ejecuta siempre y deja claro que el programa continúa.
    """
    print(f"\n[Operación {numero}] {descripcion}")
    try:
        resultado = accion(*args, **kwargs)
    except ErrorSoftwareFJ as error:
        # Error propio del sistema: se registra y se muestra al usuario.
        registrar_error(f"Operación {numero} falló: {descripcion}", error)
        print(f"  [ERROR CONTROLADO] {error}")
        if error.__cause__ is not None:
            print(f"  [CAUSA] {error.__cause__}")
    except Exception as error:
        # Respaldo para cualquier error no previsto a futuro.
        registrar_error(f"Operación {numero} falló de forma inesperada", error)
        print(f"  [ERROR NO ESPERADO] {error}")
    else:
        # Solo llega aquí si la operación terminó sin lanzar excepciones.
        registrar_evento(f"Operación {numero} completada: {descripcion}")
        print("  [OK] Operación completada.")
        if resultado is not None:
            print(f"  [RESULTADO] {resultado}")
        return resultado
    finally:
        # Se ejecute bien o mal, el programa sigue con la siguiente operación.
        print("  >>> [FIN] El programa continúa con la siguiente operación.")
#======================================================================================================================


#======================================================================================================================
# ACCIONES DE LA SIMULACIÓN
#======================================================================================================================
# Cada función encapsula una operación y se pasa a ejecutar_operacion().
# Se definen con def para que el flujo del programa sea más explícito.

def accion_cliente_valido():
    """Crea un cliente con datos válidos (operación 1)."""
    return Cliente("Ana Pérez", "35488998", "ana@gmail.com", "3001234567")


def accion_cliente_correo_invalido():
    """Intenta crear un cliente con correo inválido (operación 2)."""
    return Cliente("Carlos Ruiz", "44345678", "correo-invalido", "3001234567")


def accion_cliente_sin_telefono():
    """Intenta crear un cliente sin teléfono (operación 3)."""
    return Cliente("Laura Gómez", "67654321", "laura@gmail.com", None)


def accion_sala_valida():
    """Crea una sala de reuniones válida (operación 4)."""
    return ReservaSala("Sala Aurora", 10, 50000, disponible=True)


def accion_sala_tarifa_invalida():
    """Intenta crear una sala con tarifa negativa (operación 5)."""
    return ReservaSala("Sala Inválida", 8, -50000)


def accion_alquiler_valido():
    """Crea un alquiler de equipo válido (operación 6)."""
    return AlquilerEquipo(
        "Laptop Dell", "Laptop", 80000, unidades=2, seguro=True
    )


def accion_asesoria_valida():
    """Crea una asesoría especializada válida (operación 7)."""
    return AsesoriaEspecializada(
        "Asesoría en redes", "Redes", 100000, nivel="senior"
    )


def accion_reserva_valida(cliente, servicio):
    """Crea, confirma y procesa una reserva válida (operación 8)."""
    reserva = Reserva(cliente, servicio, 2)
    reserva.confirmar(impuesto=0.19)
    print(f"  [HISTORIAL] {list(cliente.historial_reservas)}")
    reserva.procesar()
    return reserva


def accion_reserva_duracion_invalida(cliente, servicio):
    """Intenta crear una reserva con duración fuera de rango (operación 9)."""
    return Reserva(cliente, servicio, 99)


def accion_confirmar_reserva(reserva, impuesto=0.0, descuento=0.0):
    """Confirma una reserva con los impuestos o descuentos indicados."""
    return reserva.confirmar(impuesto=impuesto, descuento=descuento)


def accion_cancelar_dos_veces(reserva):
    """Cancela una reserva y luego intenta cancelarla otra vez (operación 11)."""
    reserva.cancelar()
    print(f"  [ESTADO] {reserva.estado.value}")
    reserva.cancelar()  # Lanza OperacionNoPermitidaError
#======================================================================================================================


#======================================================================================================================
# PROGRAMA PRINCIPAL
#======================================================================================================================
def main():
    """Ejecuta la simulación completa del sistema Software FJ."""

    # Encabezado visual del programa.
    print("=" * 90)
    print("SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS")
    print("Software FJ - Fase 4")
    print("=" * 90)

    # LISTAS INTERNAS DEL SISTEMA.
    clientes = []
    servicios = []
    reservas = [] 

    # ======================================================================
    # OPERACIONES CON CLIENTES
    # ======================================================================
    print("\n--- OPERACIONES CON CLIENTES ---")

    # Operación 1: registro válido.
    cliente_valido = ejecutar_operacion(
        1,
        "Registrar un cliente con datos válidos",
        accion_cliente_valido,
    )
    if cliente_valido is not None:
        clientes.append(cliente_valido)

    # Operación 2: correo con formato inválido.
    ejecutar_operacion(
        2,
        "Registrar un cliente con correo inválido",
        accion_cliente_correo_invalido,
    )

    # Operación 3: falta un dato obligatorio.
    ejecutar_operacion(
        3,
        "Registrar un cliente sin teléfono",
        accion_cliente_sin_telefono,
    )

    # ======================================================================
    # OPERACIONES CON SERVICIOS
    # ======================================================================
    print("\n--- OPERACIONES CON SERVICIOS ---")

    # Operación 4: sala válida.
    sala_valida = ejecutar_operacion(
        4,
        "Crear una sala de reuniones válida",
        accion_sala_valida,
    )
    if sala_valida is not None:
        servicios.append(sala_valida)

    # Operación 5: servicio con tarifa inválida.
    ejecutar_operacion(
        5,
        "Crear una sala con tarifa negativa",
        accion_sala_tarifa_invalida,
    )

    # Operación 6: alquiler de equipo válido.
    equipo_valido = ejecutar_operacion(
        6,
        "Crear un alquiler de equipo válido",
        accion_alquiler_valido,
    )
    if equipo_valido is not None:
        servicios.append(equipo_valido)

    # Operación 7: asesoría especializada válida.
    asesoria_valida = ejecutar_operacion(
        7,
        "Crear una asesoría especializada válida",
        accion_asesoria_valida,
    )
    if asesoria_valida is not None:
        servicios.append(asesoria_valida)

    # ======================================================================
    # OPERACIONES CON RESERVAS
    # ======================================================================
    print("\n--- OPERACIONES CON RESERVAS ---")

    # Operación 8: reserva válida, confirmada con impuesto y procesada.
    reserva_valida = ejecutar_operacion(
        8,
        "Crear, confirmar y procesar una reserva válida",
        accion_reserva_valida,
        cliente_valido,
        sala_valida,
    )
    if reserva_valida is not None:
        reservas.append(reserva_valida)

    # Operación 9: duración fuera del rango permitido para la sala.
    ejecutar_operacion(
        9,
        "Crear una reserva con duración fuera de rango",
        accion_reserva_duracion_invalida,
        cliente_valido,
        sala_valida,
    )

    # Operación 10: servicio no disponible al confirmar.
    sala_cerrada = ReservaSala("Sala Cerrada", 5, 40000, disponible=False)
    reserva_cerrada = Reserva(cliente_valido, sala_cerrada, 2)
    reservas.append(reserva_cerrada)
    ejecutar_operacion(
        10,
        "Confirmar una reserva con servicio no disponible",
        accion_confirmar_reserva,
        reserva_cerrada,
    )

    # Operación 11: cancelar una reserva y volver a intentar cancelarla.
    reserva_cancelada = Reserva(cliente_valido, sala_valida, 1)
    reservas.append(reserva_cancelada)
    ejecutar_operacion(
        11,
        "Cancelar una reserva y volver a intentar cancelarla",
        accion_cancelar_dos_veces,
        reserva_cancelada,
    )

    # Operación 12: descuento fuera del máximo permitido.
    reserva_descuento = Reserva(cliente_valido, sala_valida, 2)
    reservas.append(reserva_descuento)
    ejecutar_operacion(
        12,
        "Confirmar una reserva con descuento inválido",
        accion_confirmar_reserva,
        reserva_descuento,
        descuento=0.80,
    )

    # ======================================================================
    # RESUMEN FINAL
    # ======================================================================
    print("\n--- RESUMEN FINAL ---")
    print(f"  Clientes registrados:  {len(clientes)}")
    print(f"  Servicios registrados: {len(servicios)}")
    print(f"  Reservas registradas:  {len(reservas)}")

    # Conteo de reservas por estado.
    conteo_estados = Counter(reserva.estado.value for reserva in reservas)
    print("\n  Reservas por estado:")
    for estado in EstadoReserva:
        print(f"    {estado.value}: {conteo_estados.get(estado.value, 0)}")

    # Ingresos de reservas confirmadas o procesadas.
    ingresos = sum(
        reserva.costo_total
        for reserva in reservas
        if reserva.estado in (EstadoReserva.CONFIRMADA, EstadoReserva.PROCESADA)
        and reserva.costo_total is not None
    )
    print(f"\n  Ingresos totales: {formato_cop(ingresos)}")
    print("\nSimulación finalizada correctamente.")


# Punto de arranque.
if __name__ == "__main__":
    main()
#====================================================================================================================
