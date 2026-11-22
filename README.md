# Software FJ · Fase 4

Sistema académico de clientes, servicios y reservas para Programación (213023),
Ingeniería de Sistemas, UNAD. Implementa POO y manejo de excepciones sin bases
de datos.

**Responsable:** Ariel Sandoval Florez (`arielsanflo1`).
**Grupo:** 213023_109. **Tutor:** Jaider Lineros.

## Ejecutar en Windows

Requiere Python 3.10 o posterior. El programa y las pruebas usan solo la biblioteca
estándar; no es necesario instalar paquetes para ejecutarlos.

```powershell
git clone https://github.com/arielsanflo1/software-fj-fase4.git
cd software-fj-fase4
python main.py
python -m unittest discover -s tests -v
```

`main.py` ejecuta 34 casos válidos e inválidos. **Un error esperado es un caso
correcto** si el sistema lo captura y el tipo coincide con lo previsto. Al final
se muestra cuántos casos cumplen. El programa termina normalmente al completar
el lote. Los clientes, servicios y reservas desaparecen al cerrar Python.

Los logs se guardan en `logs/software_fj.log` y se agregan al archivo existente.
Incluyen hora, nivel, operación y traceback de los errores, incluido su
encadenamiento. Los logs locales no se versionan; hay una ejecución de muestra
en `evidencias/simulacion.log` y sus resultados en `evidencias/resultados.csv`.

## Notebook

Abra `Fase4_SoftwareFJ.ipynb` en Jupyter Notebook, JupyterLab o VS Code, desde la
carpeta del proyecto. Seleccione un kernel Python 3.10+ y use **Restart Kernel
and Run All / Reiniciar kernel y ejecutar todo**. Si utiliza Anaconda, puede
abrir Jupyter desde Navigator. El notebook importa los módulos del repositorio:
debe descargarse la carpeta completa, no solo el archivo `.ipynb`.

El notebook presenta el diseño, ejemplos polimórficos, encadenamiento, las 34
simulaciones y la consulta del log. Sus salidas deben regenerarse cuando cambie
el programa. Para abrir notebooks se necesita Jupyter o una extensión compatible;
esto no es una dependencia de la aplicación.

## Organización

```text
software_fj/modelo.py       Entidades, validaciones, estados y listas
software_fj/ejecucion.py    Captura por operación y logging
software_fj/simulaciones.py Casos con resultados esperados
main.py                    Ejecución del lote
Fase4_SoftwareFJ.ipynb      Explicación y ejecución secuencial
tests/test_sistema.py      Pruebas de invariantes y continuidad
docs/MATRIZ_REQUISITOS.md   Relación con anexo y rúbrica
evidencias/                Resultados reales de una ejecución
```

## Diseño y reglas

`Entidad` define identidad y descripción. `Cliente` encapsula los datos de
contacto. `Servicio` es abstracta; `Sala`, `Equipo` y `Asesoria` sobrescriben
validación, descripción y cálculo. `Reserva` controla sus transiciones y
`Sistema` coordina las listas internas.

La tarifa es por hora, en COP. Los equipos multiplican por unidades del lote.
El total es `base × (1 − descuento) × (1 + impuesto)` y se redondea a dos
decimales con `ROUND_HALF_UP`. Son proporciones entre 0 y 1. Por ejemplo:
`calcular_costo(2, impuesto='0.19', descuento='0.10')`.

Las variantes del costo se implementan con parámetros opcionales, como permite
el anexo. Esto es distinto de la sobrescritura de métodos en las subclases;
Python no selecciona automáticamente entre varias definiciones del mismo nombre.

No hay agenda por fechas: cada servicio admite una reserva confirmada activa.
Cancelar o procesar libera el recurso. Ver el alcance completo en
[la matriz de requisitos](docs/MATRIZ_REQUISITOS.md).

## Estado de entrega

La implementación cuenta con 34 casos comprobados y 13 pruebas automatizadas.
El informe académico se preparó en Word y PDF con formato APA 7 y se conserva
por separado. Antes de entregar, falta revisar la documentación línea por línea
y confirmar en el campus el formato final: la guía pide PDF y una descripción
menciona comprimido con `.ipynb`. El desarrollo se presenta de forma individual.

## Materiales de la actividad

- UNAD: Anexo 3, guía y rúbrica de Fase 4 suministrados por el estudiante.
- Python Software Foundation: [Errores y excepciones](https://docs.python.org/es/3.12/tutorial/errors.html).
- Python Software Foundation: [Clases](https://docs.python.org/es/3.12/tutorial/classes.html).
- Python Software Foundation: [logging](https://docs.python.org/es/3.12/library/logging.html).

Estos enlaces son material de consulta. Las referencias APA del informe se
prepararán a partir de las fuentes efectivamente revisadas.
