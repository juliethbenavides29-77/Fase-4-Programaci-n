#======================================================================================================================
# Nombre: Luis Eduardo Vidal Hinestroza
# Grupo: 353
# Curso: Programación
# Fase 4 - componente práctico
# Sistema Integral de Gestión de Clientes, Servicios y Reservas
# Archivo: End_software_FJ.py
# Descripción: Programa principal del sistema. Aquí se integran las clases del core
#              (software_fj_core.py), se implementa la clase Reserva y se simulan las
#              operaciones del sistema.
#======================================================================================================================

#======================================================================================================================
# IMPORTACIONES
#======================================================================================================================
from enum import Enum  # Enumeración de los estados de una reserva

# Clases y funciones del núcleo que se usan en esta etapa.
from software_fj_core import (
    Cliente,
    Servicio,
    ReservaSala,
    EntidadBase,
    ParametroFaltanteError,
    ServicioInvalidoError,
    ReservaInvalidaError,
    formato_cop,
    registrar_evento,
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

    # ======================= Se implementa el método abstracto describir() =====================
    def describir(self):
        """Devuelve un texto con los datos principales de la reserva."""
        # Calculo de costo aun no implementado.
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
# PROGRAMA PRINCIPAL
#======================================================================================================================
def main():
    """Punto de entrada del programa. Por ahora solo valida la estructura inicial."""

    # Encabezado visual del programa.
    print("=" * 90)
    print("SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS")
    print("Software FJ - Fase 4")
    print("=" * 90)

    # Se muestran los estados definidos para una reserva.
    print("\nEstados de reserva disponibles:")
    for estado in EstadoReserva:
        print(f"  - {estado.value}")

    # Verificamos si el core esta disponible mediante la importacion de las clases: Cliente, Servicio y formato_cop.
    print("\nVerificación del núcleo:")
    print(f"  - Cliente:  {Cliente.__name__}")
    print(f"  - Servicio: {Servicio.__name__}")
    print(f"  - Formato de moneda: {formato_cop(150000)}")

    # ======================================================================
    # PRUEBA TEMPORAL DE LA CLASE RESERVA
    # Esta sección se quitará cuando se implemente la simulación completa.
    # ======================================================================
    print("\nPrueba temporal de la clase Reserva:")

    # Se crean un cliente y una sala válidos para probar la reserva.
    cliente_prueba = Cliente("Ana Pérez", "110788998", "ana@gmail.com", "3001234567")
    sala_prueba = ReservaSala("Sala Aurora", 10, 50000, disponible=True)

    # Caso válido: 2 horas están dentro del rango permitido para una sala.
    reserva_prueba = Reserva(cliente_prueba, sala_prueba, 2)
    print(f"  [OK] {reserva_prueba}")

    # Caso inválido: 99 horas exceden el máximo de la sala.
    try:
        Reserva(cliente_prueba, sala_prueba, 99)
    except ReservaInvalidaError as error:
        print(f"  [TEST DE ERROR] {error}")
        print(f"  -> [CAUSA] {error.__cause__}")

    # Caso inválido: el cliente no es un objeto Cliente.
    try:
        Reserva("no es un cliente", sala_prueba, 2)
    except ReservaInvalidaError as error:
        print(f"  [TEST DE ERROR] {error}")

    # Caso inválido: falta el servicio.
    try:
        Reserva(cliente_prueba, None, 2)
    except ParametroFaltanteError as error:
        print(f"  [TEST DE ERROR] {error}")

    # Mensaje de cierre de esta segunda etapa.
    print("\nPrueba de la estructura inicial y de la clase Reserva terminada.\n")


# Punto de arranque.
if __name__ == "__main__":
    main()
#======================================================================================================================
