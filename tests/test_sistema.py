"""Pruebas de reglas e invariantes; no requieren paquetes externos."""

from decimal import Decimal
import tempfile
from pathlib import Path
import unittest

from software_fj.ejecucion import configurar_log, ejecutar
from software_fj.modelo import (
    Asesoria, Cliente, DatoInvalido, Entidad, Equipo, EstadoReserva,
    OperacionNoPermitida, Sala, Servicio, ServicioNoDisponible, Sistema,
)
from software_fj.simulaciones import simular


class PruebasSistema(unittest.TestCase):
    def setUp(self):
        self.sistema = Sistema()
        self.cliente = self.sistema.registrar_cliente(
            'C1', 'Ana Ejemplo', 'ana@example.com', '3001234567')
        self.sala = self.sistema.registrar_servicio(Sala('S1', 'Sala', 50000, 5))

    def test_abstracciones_no_instanciables(self):
        with self.assertRaises(TypeError):
            Entidad('X')
        with self.assertRaises(TypeError):
            Servicio('S', 'Servicio', 10)

    def test_identificador_y_listas_protegidos(self):
        with self.assertRaises(AttributeError):
            self.cliente.identificador = 'otro'
        copia = self.sistema.clientes + (self.cliente,)
        self.assertEqual(len(copia), 2)
        self.assertEqual(len(self.sistema.clientes), 1)

    def test_actualizacion_contacto_atomica(self):
        with self.assertRaises(DatoInvalido):
            self.cliente.actualizar_contacto('nuevo@example.com', 'abc')
        self.assertEqual(self.cliente.correo, 'ana@example.com')
        self.assertEqual(self.cliente.telefono, '3001234567')

    def test_polimorfismo_y_variantes_costos(self):
        servicios = [self.sala, Equipo('E', 'Equipo', 10000, 2),
                     Asesoria('A', 'Asesoría', 80000, 'Python')]
        self.assertEqual([s.calcular_costo(2) for s in servicios],
                         [Decimal('100000'), Decimal('40000'), Decimal('160000')])
        self.assertEqual(self.sala.calcular_costo(2, impuesto='.19', descuento='.10'),
                         Decimal('107100.00'))

    def test_descuento_total_y_redondeo(self):
        self.assertEqual(self.sala.calcular_costo(1, descuento=1), Decimal('0.00'))
        self.assertEqual(Sala('S', 'Sala', '0.005', 1).calcular_costo(1), Decimal('0.01'))

    def test_valores_no_finitos_booleanos_y_limites(self):
        for valor in [True, False, 0, -1, 'NaN', 'Infinity', None, 'dos', 9]:
            with self.subTest(valor=valor), self.assertRaises(DatoInvalido):
                self.sala.calcular_costo(valor)
        self.assertEqual(self.sala.calcular_costo(8), Decimal('400000.00'))

    def test_limites_especializados(self):
        for servicio, limite in [(Equipo('E', 'E', 1, 1), 24),
                                  (Asesoria('A', 'A', 1, 'Python'), 4)]:
            self.assertEqual(servicio.calcular_costo(limite), Decimal(limite))
            with self.assertRaises(DatoInvalido):
                servicio.calcular_costo(limite + 1)

    def test_encadenamiento_preserva_causa(self):
        with self.assertRaises(DatoInvalido) as capturada:
            self.sala.calcular_costo('dos')
        self.assertIsNotNone(capturada.exception.__cause__)

    def test_error_de_calculo_no_modifica_reserva(self):
        reserva = self.sistema.crear_reserva('R1', 'C1', 'S1', 2)
        self.sistema.confirmar_reserva('R1')
        with self.assertRaises(DatoInvalido):
            self.sistema.procesar_reserva('R1', descuento=2)
        self.assertIs(reserva.estado, EstadoReserva.CONFIRMADA)
        self.assertIsNone(reserva.total)
        self.assertEqual(self.sistema.procesar_reserva('R1'), Decimal('100000.00'))

    def test_ocupacion_y_liberacion_por_cancelacion(self):
        self.sistema.crear_reserva('R1', 'C1', 'S1', 1)
        self.sistema.crear_reserva('R2', 'C1', 'S1', 1)
        self.sistema.confirmar_reserva('R1')
        with self.assertRaises(ServicioNoDisponible):
            self.sistema.confirmar_reserva('R2')
        self.sistema.cancelar_reserva('R1')
        self.sistema.confirmar_reserva('R2')

    def test_no_procesar_pendiente_ni_doble_cobro(self):
        self.sistema.crear_reserva('R1', 'C1', 'S1', 1)
        with self.assertRaises(OperacionNoPermitida):
            self.sistema.procesar_reserva('R1')
        self.sistema.confirmar_reserva('R1')
        self.sistema.procesar_reserva('R1')
        with self.assertRaises(OperacionNoPermitida):
            self.sistema.procesar_reserva('R1')
        with self.assertRaises(OperacionNoPermitida):
            self.sistema.cancelar_reserva('R1')

    def test_fallo_inesperado_y_continuidad_con_log(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'eventos.log'
            logger = configurar_log(ruta)
            fallo = ejecutar('Fallo inesperado', lambda: 1 / 0, logger)
            exito = ejecutar('Operación posterior', lambda: 42, logger)
            for handler in logger.handlers:
                handler.close()
            contenido = ruta.read_text(encoding='utf-8')
            self.assertFalse(fallo.correcto)
            self.assertEqual(exito.valor, 42)
            self.assertIn('ZeroDivisionError', contenido)
            self.assertIn('EXITO | Operación posterior', contenido)
            self.assertIn('FIN | Fallo inesperado', contenido)

    def test_lote_completo_y_todos_los_eventos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'simulacion.log'
            sistema, filas = simular(ruta, mostrar=False)
            logger = configurar_log(ruta)
            for handler in logger.handlers:
                handler.close()
            contenido = ruta.read_text(encoding='utf-8')
            self.assertEqual(len(filas), 34)
            self.assertTrue(all(fila['cumple'] for fila in filas))
            self.assertEqual(len(sistema.reservas), 4)
            for fila in filas:
                self.assertIn('INICIO | ' + fila['caso'], contenido)
                self.assertIn('FIN | ' + fila['caso'], contenido)
                marca = 'EXITO' if fila['esperado'] == 'Éxito' else (
                    'ERROR_INESPERADO' if fila['esperado'] == 'TypeError' else 'ERROR_CONTROLADO')
                self.assertIn(marca + ' | ' + fila['caso'], contenido)


if __name__ == '__main__':
    unittest.main()
