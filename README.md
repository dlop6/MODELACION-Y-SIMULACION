# Logística del Valle — Práctica 4

Rutas óptimas (Dijkstra + Yen) y simulación de eventos discretos de la flota de entregas desde la bodega `N01` hacia `N08`, `N19`, `N34` y `N40`. El enunciado y la matriz de tiempos están en [docs/](docs/).

## Instalación

Requiere Python 3.11 o superior. Los comandos son para PowerShell y se corren desde la raíz del repo.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Uso

| Acción | Comando |
|---|---|
| Correr los tests | `pytest` |
| Exportar CSV y PNG a `resultados/` | `python -m logistica.cli` (opciones: `--help`) |
| Abrir la app | `streamlit run src/logistica/app.py` → http://localhost:8501 |

La app tiene cuatro pestañas:

- **red**: el grafo y el editor de incidentes (cambiar el tiempo de un tramo o cerrarlo).
- **rutas**: la comparación por destino.
- **simulación**: una corrida con las dos políticas sobre los mismos pedidos.
- **experimentos**: las réplicas y el barrido de vehículos, con descarga de CSV.

## Supuestos del modelo

- Los pedidos llegan según un proceso de Poisson (tiempos entre llegadas exponenciales) y el destino se elige al azar con la misma probabilidad para los 4.
- La cola es FIFO. Cada vehículo lleva un solo pedido y regresa a `N01` antes de tomar otro.
- Política **actual**: la ruta de la hoja de despacho, y el regreso por el mismo camino al revés.
- Política **algoritmo**: Dijkstra calculado por separado para la ida y para el regreso, porque la red es asimétrica.
- Una entrega es puntual si `entrega − solicitud ≤ 75 min`. El tiempo de descarga en destino es configurable y por defecto vale 0.
- **Utilización** = tiempo ocupado / (vehículos × instante en que vuelve el último vehículo).
- **Tiempo extra** = max(0, regreso del último vehículo − duración de la recepción).
- Un incidente vial aplica a toda la corrida. Si cierra un tramo de una ruta actual, esa política queda inválida y no se simula.
- En cada réplica, las dos políticas reciben los mismos pedidos (misma semilla).

## Estructura

```
src/logistica/   red → rutas → politicas → simulacion → experimentos → (cli | app)
tests/           un archivo de tests por módulo
docs/            enunciado y matriz de adyacencia
```
