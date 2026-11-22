# Matriz de requisitos y comprobación

Esta matriz relaciona el Anexo 3, la guía y la rúbrica con evidencias concretas.
No constituye una calificación ni garantiza puntaje.

| Requisito | Implementación | Verificación |
|---|---|---|
| Abstracción general | `Entidad(ABC)` | Prueba de no instanciación |
| Cliente encapsulado | Propiedades y actualización validada de contacto | Actualización inválida conserva datos anteriores |
| Servicio abstracto y tres derivados | `Servicio`, `Sala`, `Equipo`, `Asesoria` | Cálculos polimórficos y límites especializados |
| Variantes del costo | Parámetros opcionales `impuesto` y `descuento` | Base, impuesto, descuento y combinación |
| Reserva y estados | Pendiente, confirmada, cancelada, procesada | Transiciones inválidas, doble procesamiento y liberación |
| Listas sin base de datos | Listas internas de `Sistema` | Propiedades devuelven tuplas; no hay persistencia del negocio |
| Excepciones personalizadas | Jerarquía `ErrorSoftwareFJ` | Casos válidos e inválidos |
| `try/except/else/finally` | `ejecucion.ejecutar` | Log de inicio, resultado y fin por operación |
| Encadenamiento | `numero`: `raise ... from causa` | Causa no nula y traceback en log |
| Mínimo diez operaciones | 34 casos en `simulaciones.py` | Se compara resultado esperado y obtenido |
| Continuidad después de errores | Frontera por operación | Casos 20–21 y 31–34; fallo inesperado en prueba |
| Log de eventos y errores | `logging`, archivo UTF-8 | Se verifica cada caso contra el log |
| Notebook secuencial | `Fase4_SoftwareFJ.ipynb` | Celdas ejecutables desde kernel limpio |
| Documentación | README, docstrings, comentarios y notebook | Revisión explicativa pendiente con el estudiante |
| GitHub | Repositorio y rama de desarrollo | Historial real, revisión mediante pull request |
| Colaboración de cinco integrantes | No se cumple: desarrollo individual declarado | Consultar al tutor; no atribuir aportes inexistentes |
| PDF de entrega | Portada, introducción, enlace, conclusiones, referencias APA | Pendiente de datos de portada y revisión del estudiante |

## Alcance y decisiones

- Moneda: COP; tarifas ficticias por hora. `Decimal` evita el error binario de `float` en dinero.
- Impuestos y descuentos son ejemplos de cálculo, no una regla tributaria aplicable a una empresa real.
- Una sala es un recurso; un servicio de equipos representa un lote reservado completo.
- Cada servicio admite una reserva confirmada activa. No hay calendario: procesar o cancelar libera ocupación.
- Las reservas pendientes son solicitudes y no bloquean el servicio. La confirmación comprueba la ocupación.
- El procesamiento simula la liquidación; no realiza cobros ni conexiones externas.
- Las validaciones de correo son básicas; no comprueban la existencia del buzón.
- Los datos de ejemplo usan `example.com`; no se registran datos de contacto en los eventos.
- Los métodos del modelo propagan los errores. La interfaz debe invocarlos mediante `ejecutar` para registrarlos y continuar.
- Si no puede abrirse o escribirse el log, se informa por consola. En ese escenario no se puede afirmar que existe un registro completo en archivo.
- Ctrl+C, cierre del intérprete y fallos del sistema operativo no se ocultan. La estabilidad demostrada corresponde a errores de ejecución de las operaciones simuladas.
- La guía solicita comentar cada línea. Esta versión usa documentación por método y bloques; requiere una revisión pedagógica línea por línea antes de considerarla entrega final.
