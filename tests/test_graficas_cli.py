import csv

import pytest
from matplotlib.figure import Figure

from logistica.cli import main
from logistica.comparacion import comparar_rutas, tabla_rutas
from logistica.escenarios import ESCENARIOS
from logistica.exportar import celda_segura, filas_a_csv
from logistica.experimentos import Parametros, barrido_vehiculos, construir_planes, correr_pareado, tabla_resumen
from logistica.graficas import fig_barrido, fig_metricas, fig_red, posiciones
from logistica.metricas import INDICADORES_CLAVE
from logistica.politicas import DESTINOS


def test_posiciones_en_grilla(red):
    pos = posiciones(red)
    assert pos["N01"] == (0, 0)
    assert pos["N08"] == (7, 0)
    assert pos["N09"] == (0, -1)
    assert pos["N40"] == (7, -4)


def test_figuras(red):
    planes, _ = construir_planes(red)
    parametros = Parametros(replicas=2)
    resumen = tabla_resumen(correr_pareado(planes, ESCENARIOS, parametros))
    barrido = tabla_resumen(barrido_vehiculos(planes, ESCENARIOS, parametros, range(7, 9)))
    assert isinstance(fig_red(red, {"ruta": ("N01", "N02", "N03")}), Figure)
    for indicador in INDICADORES_CLAVE:
        assert isinstance(fig_metricas(resumen, indicador), Figure)
        assert isinstance(fig_barrido(barrido, indicador), Figure)


def test_tabla_rutas(red):
    filas = tabla_rutas(comparar_rutas(red))
    n40 = {f["opcion"]: f for f in filas if f["destino"] == "N40"}
    assert n40["actual"]["ruta_ida"].startswith("N01-N02")
    assert n40["actual"]["ahorro_ciclo_vs_actual"] == 0
    assert n40["algoritmo"]["ahorro_ciclo_vs_actual"] == 186 - 108
    assert n40["actual"]["puntual_sin_espera"] is False
    cerrada = tabla_rutas(comparar_rutas(red.sin_arco("N07", "N08")))
    assert next(f for f in cerrada if f["destino"] == "N08")["ahorro_ciclo_vs_actual"] is None


@pytest.mark.parametrize("valor, esperado", [("=1+1", "'=1+1"), ("-x", "'-x"), ("N01", "N01"), (-8, -8)])
def test_celda_segura(valor, esperado):
    assert celda_segura(valor) == esperado


def test_filas_a_csv():
    assert filas_a_csv([]) == ""
    assert filas_a_csv([{"a": 1, "b": "=x"}]) == "a,b\n1,'=x\n"


def test_cli_de_punta_a_punta(tmp_path, capsys):
    codigo = main(["--salida", str(tmp_path), "--replicas", "2", "--flota-min", "7", "--flota-max", "8"])
    assert codigo == 0
    esperados = {"rutas.csv", "replicas.csv", "resumen.csv", "barrido.csv", "incidentes_rutas.csv",
                 "incidentes_resumen.csv", "red.png"}
    esperados |= {f"rutas_{d}.png" for d in DESTINOS}
    esperados |= {f"{p}_{i}.png" for p in ("metricas", "barrido") for i in INDICADORES_CLAVE}
    assert esperados <= {p.name for p in tmp_path.iterdir()}
    with (tmp_path / "replicas.csv").open(encoding="utf-8") as archivo:
        assert len(list(csv.DictReader(archivo))) == len(ESCENARIOS) * 2 * 2
    assert str(tmp_path) in capsys.readouterr().out


@pytest.mark.parametrize(
    "argumentos",
    [["--replicas", "0"], ["--vehiculos", "500"], ["--duracion", "abc"], ["--flota-min", "9", "--flota-max", "8"]],
)
def test_cli_rechaza_argumentos(tmp_path, argumentos):
    with pytest.raises(SystemExit) as salida:
        main(["--salida", str(tmp_path), *argumentos])
    assert salida.value.code != 0
