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
