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

# Clases y funciones del core para probar la importacion
from software_fj_core import Cliente, Servicio, formato_cop
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

    # Mensaje de cierre de esta primera etapa.
    print("\nEstructura inicial lista ;D \n")


# Punto de arranque.
if __name__ == "__main__":
    main()
#======================================================================================================================
