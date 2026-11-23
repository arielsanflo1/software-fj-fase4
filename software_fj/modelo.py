"""Entidades, reglas de negocio y excepciones de Software FJ.

Los datos viven en memoria. Solo la capa de ejecución escribe eventos y
errores en un log. Las entidades lanzan excepciones; no ocultan los errores.
"""

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
import re


class ErrorSoftwareFJ(Exception):
    """Base común para los errores controlados del dominio."""


class DatoInvalido(ErrorSoftwareFJ):
    """Un dato no cumple las condiciones de la operación."""


class Duplicado(ErrorSoftwareFJ):
    """El identificador ya está registrado."""


class NoEncontrado(ErrorSoftwareFJ):
    """La entidad solicitada no pertenece al sistema."""


class ServicioNoDisponible(ErrorSoftwareFJ):
    """El servicio está deshabilitado u ocupado."""


class OperacionNoPermitida(ErrorSoftwareFJ):
    """El estado actual impide la transición solicitada."""


def texto(valor, campo):
    """Rechaza valores ausentes, tipos incorrectos y espacios vacíos."""
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalido(f"{campo}: se requiere texto no vacío.")
    return valor.strip()


def numero(valor, campo, minimo=Decimal('0'), maximo=None, estricto=False):
    """Convierte a Decimal y conserva la causa de un fallo de conversión."""
    if isinstance(valor, bool):
        raise DatoInvalido(f"{campo}: un booleano no es un número válido.")
    try:
        resultado = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as causa:
        # 'from' permite consultar tanto el error de negocio como su causa.
        raise DatoInvalido(f"{campo}: debe ser numérico.") from causa
    if not resultado.is_finite():
        raise DatoInvalido(f"{campo}: debe ser un número finito.")
    if resultado < minimo or (estricto and resultado == minimo):
        raise DatoInvalido(f"{campo}: valor inferior al límite permitido.")
    if maximo is not None and resultado > maximo:
        raise DatoInvalido(f"{campo}: supera el límite {maximo}.")
    return resultado


def entero_positivo(valor, campo):
    """Acepta cantidades enteras mayores que cero, excluyendo bool."""
    if type(valor) is not int or valor <= 0:
        raise DatoInvalido(f"{campo}: se requiere un entero positivo.")
    return valor


class Entidad(ABC):
    """Abstracción general: toda entidad tiene identidad y descripción."""

    def __init__(self, identificador):
        self.__identificador = texto(identificador, 'Identificador')

    @property
    def identificador(self):
        """La identidad es de solo lectura para evitar cambios accidentales."""
        return self.__identificador

    @abstractmethod
    def describir(self):
        """Obliga a cada entidad concreta a proporcionar una descripción."""


class Cliente(Entidad):
    """Encapsula datos personales y valida antes de modificar el objeto."""

    def __init__(self, identificador, nombre, correo, telefono):
        super().__init__(identificador)
        self.__nombre = texto(nombre, 'Nombre')
        self.actualizar_contacto(correo, telefono)

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    @property
    def telefono(self):
        return self.__telefono

    def actualizar_contacto(self, correo, telefono):
        """Si un campo falla, ninguno de los dos datos anteriores cambia."""
        correo_validado = texto(correo, 'Correo')
        telefono_validado = texto(telefono, 'Teléfono')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo_validado):
            raise DatoInvalido('Correo: formato inválido.')
        if not re.fullmatch(r'\+?[0-9]{7,15}', telefono_validado):
            raise DatoInvalido('Teléfono: debe contener de 7 a 15 dígitos.')
        self.__correo, self.__telefono = correo_validado, telefono_validado

    def describir(self):
        # Se evita exponer correo y teléfono en los logs de demostración.
        return f'Cliente {self.identificador}: {self.nombre}'


class Servicio(Entidad):
    """Contrato abstracto para servicios con tarifa por hora en COP."""

    def __init__(self, identificador, nombre, tarifa, disponible=True):
        super().__init__(identificador)
        self.__nombre = texto(nombre, 'Nombre del servicio')
        self.__tarifa = numero(tarifa, 'Tarifa', estricto=True)
        if type(disponible) is not bool:
            raise DatoInvalido('Disponible: debe ser True o False.')
        self.__disponible = disponible

    @property
    def nombre(self):
        return self.__nombre

    @property
    def tarifa(self):
        return self.__tarifa

    @property
    def disponible(self):
        return self.__disponible

    def cambiar_disponibilidad(self, disponible):
        if type(disponible) is not bool:
            raise DatoInvalido('Disponible: debe ser True o False.')
        self.__disponible = disponible

    @abstractmethod
    def validar_parametros(self, duracion):
        """Cada especialización impone límites propios de duración."""

    @abstractmethod
    def calcular_costo(self, duracion, *, impuesto=0, descuento=0):
        """Variantes por argumentos opcionales, como solicita el anexo.

        Python no conserva varias definiciones del mismo método según su
        firma. Se usa una única firma con parámetros opcionales; esto es
        diferente de la sobrescritura aplicada por las subclases.
        """

    def _total(self, base, impuesto, descuento):
        # Son proporciones: 0.19 significa 19 %. El descuento se aplica primero.
        tasa = numero(impuesto, 'Impuesto', maximo=Decimal('1'))
        rebaja = numero(descuento, 'Descuento', maximo=Decimal('1'))
        return (base * (1 - rebaja) * (1 + tasa)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)


class Sala(Servicio):
    """Una sala reservable, con capacidad y máximo ocho horas por reserva."""

    def __init__(self, identificador, nombre, tarifa, capacidad, disponible=True):
        super().__init__(identificador, nombre, tarifa, disponible)
        self.__capacidad = entero_positivo(capacidad, 'Capacidad')

    def validar_parametros(self, duracion):
        return numero(duracion, 'Horas de sala', maximo=Decimal('8'), estricto=True)

    def calcular_costo(self, duracion, *, impuesto=0, descuento=0):
        horas = self.validar_parametros(duracion)
        return self._total(self.tarifa * horas, impuesto, descuento)

    def describir(self):
        return f'Sala {self.nombre}; capacidad {self.__capacidad}; COP {self.tarifa}/hora'


class Equipo(Servicio):
    """Un lote de equipos se reserva completo; máximo 24 horas."""

    def __init__(self, identificador, nombre, tarifa, unidades, disponible=True):
        super().__init__(identificador, nombre, tarifa, disponible)
        self.__unidades = entero_positivo(unidades, 'Unidades')

    def validar_parametros(self, duracion):
        return numero(duracion, 'Horas de equipo', maximo=Decimal('24'), estricto=True)

    def calcular_costo(self, duracion, *, impuesto=0, descuento=0):
        horas = self.validar_parametros(duracion)
        return self._total(self.tarifa * horas * self.__unidades, impuesto, descuento)

    def describir(self):
        return f'Equipo {self.nombre}; {self.__unidades} unidades; COP {self.tarifa}/unidad/hora'


class Asesoria(Servicio):
    """Asesoría de una especialidad, con máximo cuatro horas por sesión."""

    def __init__(self, identificador, nombre, tarifa, especialidad, disponible=True):
        super().__init__(identificador, nombre, tarifa, disponible)
        self.__especialidad = texto(especialidad, 'Especialidad')

    def validar_parametros(self, duracion):
        return numero(duracion, 'Horas de asesoría', maximo=Decimal('4'), estricto=True)

    def calcular_costo(self, duracion, *, impuesto=0, descuento=0):
        horas = self.validar_parametros(duracion)
        return self._total(self.tarifa * horas, impuesto, descuento)

    def describir(self):
        return f'Asesoría {self.nombre}; {self.__especialidad}; COP {self.tarifa}/hora'


class EstadoReserva(Enum):
    PENDIENTE = 'pendiente'
    CONFIRMADA = 'confirmada'
    CANCELADA = 'cancelada'
    PROCESADA = 'procesada'


class Reserva(Entidad):
    """Reserva con transiciones controladas y relaciones encapsuladas."""

    def __init__(self, identificador, cliente, servicio, duracion):
        super().__init__(identificador)
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise DatoInvalido('La reserva requiere un Cliente y un Servicio.')
        self.__duracion = servicio.validar_parametros(duracion)
        self.__cliente, self.__servicio = cliente, servicio
        self.__estado = EstadoReserva.PENDIENTE
        self.__total = None

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def estado(self):
        return self.__estado

    @property
    def total(self):
        return self.__total

    def confirmar(self):
        if self.estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitida('Solo se confirma una reserva pendiente.')
        if not self.servicio.disponible:
            raise ServicioNoDisponible('El servicio está deshabilitado.')
        self.__estado = EstadoReserva.CONFIRMADA

    def cancelar(self):
        if self.estado not in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA):
            raise OperacionNoPermitida('No es posible cancelar en el estado actual.')
        self.__estado = EstadoReserva.CANCELADA

    def procesar(self, *, impuesto=0, descuento=0):
        if self.estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitida('Solo se procesa una reserva confirmada.')
        if not self.servicio.disponible:
            raise ServicioNoDisponible('El servicio está deshabilitado.')
        # El cálculo se completa antes de modificar el estado: un error no cobra.
        total = self.servicio.calcular_costo(
            self.__duracion, impuesto=impuesto, descuento=descuento)
        self.__total, self.__estado = total, EstadoReserva.PROCESADA
        return total

    def describir(self):
        return (f'Reserva {self.identificador}: cliente {self.cliente.identificador}, '
                f'servicio {self.servicio.identificador}, {self.__duracion} h, '
                f'estado {self.estado.value}')


class Sistema:
    """Coordina listas internas y evita duplicados y ocupación simultánea.

    Simulación sin agenda: cada servicio admite una reserva confirmada activa.
    Cancelar o procesar libera su ocupación; no se implementan fechas ni pagos.
    """

    def __init__(self):
        self.__clientes, self.__servicios, self.__reservas = [], [], []

    @property
    def clientes(self):
        return tuple(self.__clientes)

    @property
    def servicios(self):
        return tuple(self.__servicios)

    @property
    def reservas(self):
        return tuple(self.__reservas)

    @staticmethod
    def _buscar(lista, identificador):
        clave = texto(identificador, 'Identificador')
        for objeto in lista:
            if objeto.identificador == clave:
                return objeto
        raise NoEncontrado(f'No existe la entidad {clave}.')

    @staticmethod
    def _agregar(lista, objeto):
        if any(item.identificador == objeto.identificador for item in lista):
            raise Duplicado(f'Identificador duplicado: {objeto.identificador}.')
        lista.append(objeto)
        return objeto

    def registrar_cliente(self, identificador, nombre, correo, telefono):
        return self._agregar(self.__clientes, Cliente(identificador, nombre, correo, telefono))

    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise DatoInvalido('Se requiere una instancia concreta de Servicio.')
        return self._agregar(self.__servicios, servicio)

    def crear_reserva(self, identificador, cliente_id, servicio_id, duracion):
        cliente = self._buscar(self.__clientes, cliente_id)
        servicio = self._buscar(self.__servicios, servicio_id)
        if not servicio.disponible:
            raise ServicioNoDisponible('El servicio solicitado está deshabilitado.')
        return self._agregar(self.__reservas, Reserva(identificador, cliente, servicio, duracion))

    def confirmar_reserva(self, identificador):
        reserva = self._buscar(self.__reservas, identificador)
        if any(otra is not reserva and otra.servicio is reserva.servicio
               and otra.estado is EstadoReserva.CONFIRMADA for otra in self.__reservas):
            raise ServicioNoDisponible('El servicio ya tiene una reserva confirmada activa.')
        reserva.confirmar()
        return reserva

    def cancelar_reserva(self, identificador):
        reserva = self._buscar(self.__reservas, identificador)
        reserva.cancelar()
        return reserva

    def procesar_reserva(self, identificador, *, impuesto=0, descuento=0):
        reserva = self._buscar(self.__reservas, identificador)
        return reserva.procesar(impuesto=impuesto, descuento=descuento)
