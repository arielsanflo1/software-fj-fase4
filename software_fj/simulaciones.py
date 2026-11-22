"""Casos reproducibles: datos ficticios, resultados esperados y aserciones."""

from .ejecucion import configurar_log, ejecutar
from .modelo import (
    Asesoria, DatoInvalido, Duplicado, Equipo, EstadoReserva,
    NoEncontrado, OperacionNoPermitida, Sala, ServicioNoDisponible, Sistema,
)


def simular(ruta_log='logs/software_fj.log', mostrar=True):
    """Ejecuta un lote nuevo; cada caso comprueba valor o clase de excepción."""
    sistema = Sistema()
    logger = configurar_log(ruta_log)
    sala = Sala('S1', 'Sala de reuniones', 50000, 10)
    equipo = Equipo('E1', 'Portátiles', 10000, 2)
    asesoria = Asesoria('A1', 'Sesión Python', 80000, 'Programación')
    filas = []

    def caso(nombre, operacion, error=None, verificar=None):
        resultado = ejecutar(nombre, operacion, logger)
        if error is None:
            cumple = resultado.correcto and (verificar is None or verificar(resultado.valor))
        else:
            cumple = not resultado.correcto and type(resultado.error) is error
        filas.append({'caso': nombre, 'esperado': error.__name__ if error else 'Éxito',
                      'obtenido': type(resultado.error).__name__ if resultado.error else 'Éxito',
                      'cumple': cumple})
        if mostrar:
            print(f"{'OK' if cumple else 'FALLO'} | {nombre} | {filas[-1]['obtenido']}")
        return resultado

    caso('01 Registrar cliente válido', lambda: sistema.registrar_cliente(
        'C1', 'Ana Ejemplo', 'ana@example.com', '3001234567'))
    caso('02 Rechazar correo inválido', lambda: sistema.registrar_cliente(
        'C2', 'Luis Ejemplo', 'correo-invalido', '3001234568'), DatoInvalido)
    caso('03 Registrar cliente tras error', lambda: sistema.registrar_cliente(
        'C2', 'Luis Ejemplo', 'luis@example.com', '3001234568'))
    caso('04 Rechazar cliente duplicado', lambda: sistema.registrar_cliente(
        'C1', 'Ana Ejemplo', 'ana@example.com', '3001234567'), Duplicado)
    caso('05 Rechazar parámetros faltantes', lambda: sistema.registrar_cliente('C3'), TypeError)
    caso('06 Registrar sala', lambda: sistema.registrar_servicio(sala))
    caso('07 Rechazar tarifa negativa', lambda: sistema.registrar_servicio(
        Equipo('E0', 'Inválido', -1, 1)), DatoInvalido)
    caso('08 Registrar equipos', lambda: sistema.registrar_servicio(equipo))
    caso('09 Rechazar especialidad vacía', lambda: sistema.registrar_servicio(
        Asesoria('A0', 'Inválida', 80000, ' ')), DatoInvalido)
    caso('10 Registrar asesoría', lambda: sistema.registrar_servicio(asesoria))
    caso('11 Rechazar capacidad inválida', lambda: Sala('S0', 'Inválida', 100, 0), DatoInvalido)
    caso('12 Registrar servicio deshabilitado', lambda: sistema.registrar_servicio(
        Sala('S2', 'Mantenimiento', 50000, 5, disponible=False)))
    caso('13 Rechazar servicio no disponible', lambda: sistema.crear_reserva(
        'R0', 'C1', 'S2', 1), ServicioNoDisponible)
    caso('14 Rechazar cliente inexistente', lambda: sistema.crear_reserva(
        'R0', 'C9', 'S1', 1), NoEncontrado)
    caso('15 Rechazar duración negativa', lambda: sistema.crear_reserva(
        'R0', 'C1', 'S1', -2), DatoInvalido)
    caso('16 Crear reserva de sala', lambda: sistema.crear_reserva('R1', 'C1', 'S1', 2))
    caso('17 Confirmar reserva de sala', lambda: sistema.confirmar_reserva('R1'))
    caso('18 Crear segunda solicitud de sala', lambda: sistema.crear_reserva('R2', 'C2', 'S1', 1))
    caso('19 Rechazar ocupación simultánea', lambda: sistema.confirmar_reserva('R2'), ServicioNoDisponible)
    caso('20 Rechazar impuesto inválido', lambda: sistema.procesar_reserva('R1', impuesto=2), DatoInvalido)
    caso('21 Procesar sala tras error: COP 107100', lambda: sistema.procesar_reserva(
        'R1', impuesto='0.19', descuento='0.10'), verificar=lambda total: str(total) == '107100.00')
    caso('22 Confirmar sala liberada', lambda: sistema.confirmar_reserva('R2'))
    caso('23 Cancelar reserva confirmada', lambda: sistema.cancelar_reserva('R2'))
    caso('24 Rechazar procesamiento cancelado', lambda: sistema.procesar_reserva('R2'), OperacionNoPermitida)
    caso('25 Crear reserva de equipos', lambda: sistema.crear_reserva('R3', 'C2', 'E1', 3))
    caso('26 Confirmar equipos', lambda: sistema.confirmar_reserva('R3'))
    caso('27 Procesar equipos: COP 60000', lambda: sistema.procesar_reserva('R3'),
         verificar=lambda total: str(total) == '60000.00')
    caso('28 Crear reserva de asesoría', lambda: sistema.crear_reserva('R4', 'C1', 'A1', '1.5'))
    caso('29 Confirmar asesoría', lambda: sistema.confirmar_reserva('R4'))
    caso('30 Procesar asesoría: COP 120000', lambda: sistema.procesar_reserva('R4'),
         verificar=lambda total: str(total) == '120000.00')
    caso('31 Rechazar conversión numérica', lambda: sala.calcular_costo('dos'), DatoInvalido,
         )
    caso('32 Rechazar cálculo no finito', lambda: sala.calcular_costo('NaN'), DatoInvalido)
    caso('33 Rechazar descuento excesivo', lambda: sala.calcular_costo(1, descuento='1.01'), DatoInvalido)
    caso('34 Operación válida final: COP 50000', lambda: sala.calcular_costo(1),
         verificar=lambda total: str(total) == '50000.00')

    # Además del resultado impreso, se verifican las invariantes del lote completo.
    assert all(fila['cumple'] for fila in filas), 'Hay resultados distintos de los esperados.'
    assert len(sistema.clientes) == 2 and len(sistema.servicios) == 4
    assert len(sistema.reservas) == 4
    assert sistema.reservas[0].estado is EstadoReserva.PROCESADA
    logger.info('RESUMEN | %s/%s casos cumplieron lo esperado', len(filas), len(filas))
    if mostrar:
        print(f'\n{len(filas)}/{len(filas)} casos cumplen. Log: {ruta_log}')
    return sistema, filas
