# Simulaciones de eventos discretos

El proyecto contiene las tres simulaciones solicitadas:

- Banco: clientes, cola FIFO y cajeros.
- Inventario: existencias, pedidos, escasez, costos y ventas.
- Máquinas de repuesto: máquinas activas, repuestos y un mecánico.

## Ejecución

Requiere Python 3.11 o posterior. Desde `ejercicio010926`:

```powershell
python -m pip install -e .
python -m simulacion examples/config.example.json
```

Los datos de `examples/config.example.json` son demostrativos y deben
reemplazarse con los valores reales.

Para comparar la simulación con datos reales:

```powershell
python -m simulacion examples/config.example.json --actual examples/actual.example.json
```

Para guardar el resultado:

```powershell
python -m simulacion examples/config.example.json --actual examples/actual.example.json --output resultado.json
```

## ¿Cuál es la utilidad de estas simulaciones?

Permiten experimentar con un sistema sin modificar el sistema real. Sirven para
estimar tiempos de espera, utilización, disponibilidad, faltantes y costos;
detectar cuellos de botella; y comparar políticas antes de invertir dinero o
afectar a usuarios reales.

## Ley de Little

La Ley de Little relaciona tres valores de un sistema estable:

```text
L = λ × W
```

- `L`: cantidad promedio de elementos dentro del sistema.
- `λ`: tasa promedio de entrada.
- `W`: tiempo promedio que un elemento permanece en el sistema.

Se utilizó así:

- Banco: clientes en el banco y clientes esperando en la cola.
- Inventario: unidades que están viajando en pedidos.
- Reparaciones: máquinas dentro del sistema de reparación.

Cada resultado muestra `L`, `λ × W` y `little_*_absolute_error`. El error debe ser
cercano a cero. Para que la validación también sea correcta al terminar una
corrida finita, `W` incluye el tiempo observado de los elementos que aún siguen
dentro del sistema al alcanzar el horizonte.

## Pruebas

```powershell
python -m pip install -e ".[dev]"
pytest
```
