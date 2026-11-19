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
    ServicioNoDisponibleError,
    OperacionNoPermitidaError,
    CalculoInconsistenteError,
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
# PROGRAMA PRINCIPAL
#======================================================================================================================
def main():
    """Ejecuta las pruebas temporales de la clase Reserva y su ciclo de vida."""

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
    # PRUEBAS TEMPORALES
    # Esta sección se reemplazará por la simulación completa mas adelante
    # ======================================================================
    print("\nPruebas tempoales")

    # --- Preparación ------------------------------------------------------
    # Se crean un cliente y una sala válidos para reutilizarlos en las pruebas.
    cliente_prueba = Cliente("Ana Pérez", "110788998", "ana@gmail.com", "3001234567")
    sala_prueba = ReservaSala("Sala Aurora", 10, 50000, disponible=True)

    # --- 1. Creación de una reserva válida --------------------------------
    print("\n1. Creación de una reserva válida")
    reserva_prueba = Reserva(cliente_prueba, sala_prueba, 2)
    print(f"  [CASO VÁLIDO] {reserva_prueba}")

    # --- 2. Errores de creación -------------------------------------------
    print("\n2. Errores de creación")

    # 2.1 Duración fuera del rango permitido para una sala.
    try:
        Reserva(cliente_prueba, sala_prueba, 99)
    except ReservaInvalidaError as error:
        print(f"  [CASO INVÁLIDO] {error}")
        print(f"  -> [CAUSA] {error.__cause__}")

    # 2.2 Cliente con un tipo inválido.
    try:
        Reserva("no es un cliente", sala_prueba, 2)
    except ReservaInvalidaError as error:
        print(f"  [CASO INVÁLIDO] {error}")

    # 2.3 Falta el servicio.
    try:
        Reserva(cliente_prueba, None, 2)
    except ParametroFaltanteError as error:
        print(f"  [CASO INVÁLIDO] {error}")

    # --- 3. Ciclo de vida exitoso -----------------------------------------
    print("\n3. Ciclo de vida exitoso")

    # 3.1 Confirmar la reserva aplicando un impuesto del 19 %.
    reserva_ciclo = Reserva(cliente_prueba, sala_prueba, 2)
    costo = reserva_ciclo.confirmar(impuesto=0.19)

    # 3.2 Mostrar el estado, el costo y el historial del cliente.
    print(f"  [CASO VÁLIDO] {reserva_ciclo}")
    print(f"  [ESTADO] {reserva_ciclo.estado.value}")
    print(f"  [COSTO] {formato_cop(costo)}")
    print(f"  [HISTORIAL] {list(cliente_prueba.historial_reservas)}")

    # 3.3 Procesar la reserva confirmada.
    reserva_ciclo.procesar()
    print(f"  [ESTADO] {reserva_ciclo.estado.value}")

    # --- 4. Cancelación exitosa -------------------------------------------
    print("\n4. Cancelación exitosa")
    reserva_cancelada = Reserva(cliente_prueba, sala_prueba, 1)
    reserva_cancelada.cancelar()
    print(f"  [CASO VÁLIDO] {reserva_cancelada}")

    # --- 5. Errores de transición -----------------------------------------
    print("\n5. Errores de transición")

    # 5.1 Cancelar una reserva que ya fue procesada.
    try:
        reserva_ciclo.cancelar()
    except OperacionNoPermitidaError as error:
        print(f"  [CASO INVÁLIDO] {error}")

    # 5.2 Cancelar dos veces la misma reserva.
    try:
        reserva_cancelada.cancelar()
    except OperacionNoPermitidaError as error:
        print(f"  [CASO INVÁLIDO] {error}")

    # 5.3 Procesar una reserva que sigue pendiente.
    reserva_pendiente = Reserva(cliente_prueba, sala_prueba, 1)
    try:
        reserva_pendiente.procesar()
    except OperacionNoPermitidaError as error:
        print(f"  [CASO INVÁLIDO] {error}")

    # Error de disponibilidad ----------------------------------------
    print("\n6. Error de disponibilidad")
    sala_cerrada = ReservaSala("Sala Cerrada", 5, 40000, disponible=False)
    reserva_cerrada = Reserva(cliente_prueba, sala_cerrada, 2)
    try:
        reserva_cerrada.confirmar()
    except ServicioNoDisponibleError as error:
        print(f"  [CASO INVÁLIDO] {error}")
        print(f"  [ESTADO] {reserva_cerrada.estado.value}")

    # Error de cálculo -----------------------------------------------
    print("\n7. Error de cálculo")
    reserva_descuento = Reserva(cliente_prueba, sala_prueba, 2)
    try:
        reserva_descuento.confirmar(descuento=0.80)
    except CalculoInconsistenteError as error:
        print(f"  [CASO INVÁLIDO] {error}")
        print(f"  [ESTADO] {reserva_descuento.estado.value}")


# Punto de arranque.
if __name__ == "__main__":
    main()
#======================================================================================================================
