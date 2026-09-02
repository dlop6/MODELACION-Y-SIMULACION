# Simulación de inventario y máquinas

Simulación de eventos discretos en Python para:

- Controlar inventario, pedidos, escasez, costos y ventas.
- Simular máquinas, repuestos y un mecánico.
- Comparar los resultados con valores reales.

## Requisitos

- Python 3.11 o posterior.

## Configuración

Edita `examples/config.example.json` y reemplaza los valores de ejemplo con los
datos del sistema real. La propiedad `seed` permite repetir exactamente una
simulación.

En el modelo de inventario, `shortage_policy` acepta:

- `lost_sales`: la demanda no atendida se pierde.
- `backorder`: la demanda no atendida queda pendiente.

Los repuestos se consideran máquinas completas almacenadas. Solo pueden fallar
cuando entran a trabajar. Las máquinas averiadas son atendidas por un único
mecánico.

## Ejecución

Desde la carpeta `ejercicio010926`:

```powershell
python -m pip install -e .
python -m simulacion examples/config.example.json
```

Para comparar con valores reales:

```powershell
python -m simulacion examples/config.example.json --actual examples/actual.example.json
```

Para guardar el resultado:

```powershell
python -m simulacion examples/config.example.json --actual examples/actual.example.json --output resultado.json
```

## Pruebas

```powershell
python -m pip install -e ".[dev]"
pytest
```

Los archivos dentro de `examples` contienen datos demostrativos, no datos
reales.
