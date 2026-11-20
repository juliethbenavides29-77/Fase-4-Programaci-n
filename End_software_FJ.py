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
def ejecutar_operacion(numero, descripcion, accion):
    """Ejecuta una operación de la simulación y controla sus errores.

    Se usa try/except/else/finally para demostrar el manejo completo:
    - try: intenta ejecutar la operación.
    - except: captura errores del dominio o errores inesperados.
    - else: se ejecuta solo si no hubo error.
    - finally: se ejecuta siempre y deja claro que el programa continúa.
    """
    print(f"\n[Operación {numero}] {descripcion}")
    try:
        resultado = accion()
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
# MEJORAR CON LAMDAS

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
#======================================================================================================================


#======================================================================================================================
# PROGRAMA PRINCIPAL
#======================================================================================================================
def main():
    """Ejecuta la simulación de operaciones de clientes y servicios."""

    # Encabezado visual del programa.
    print("=" * 90)
    print("SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS")
    print("Software FJ - Fase 4")
    print("=" * 90)

    # LISTAS INTERNAS DEL SISTEMA.
    clientes = []
    servicios = []
    # reservas = [] 

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

    # Fin de la simulación.
    print("\nOperaciones de clientes y servicios completadas.")
    print(f"  Clientes registrados:  {len(clientes)}")
    print(f"  Servicios registrados: {len(servicios)}")


# Punto de arranque.
if __name__ == "__main__":
    main()
#======================================================================================================================
