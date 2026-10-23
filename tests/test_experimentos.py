import pytest

from logistica import experimentos
from logistica.escenarios import ESCENARIOS
from logistica.experimentos import (
    Parametros,
    barrido_vehiculos,
    construir_planes,
    correr_pareado,
    tabla_corridas,
    tabla_resumen,
)
from logistica.red import Incidente, aplicar_incidentes


def test_planes_validos(red):
    planes, errores = construir_planes(red)
    assert set(planes) == {"actual", "algoritmo"}
    assert errores == {}


def test_ruta_actual_cerrada_deja_solo_algoritmo(red):
    planes, errores = construir_planes(aplicar_incidentes(red, [Incidente("N07", "N08")]))
    assert set(planes) == {"algoritmo"}
    assert "N07->N08" in errores["actual"]


def test_incidentes_en_orden(red):
    nueva = aplicar_incidentes(red, [Incidente("N09", "N17", 18), Incidente("N01", "N17")])
    assert nueva.tiempo("N09", "N17") == 18
    assert nueva.tiempo("N01", "N17") is None
    assert Incidente("N01", "N17").describir() == "N01->N17 cerrado"
    assert Incidente("N09", "N17", 18).describir() == "N09->N17 18 min"


def test_mismos_pedidos_en_cada_pareja(red, monkeypatch):
    vistos = []
    original = experimentos.simular

    def espiar(pedidos, plan, config):
        vistos.append(pedidos)
        return original(pedidos, plan, config)

    monkeypatch.setattr(experimentos, "simular", espiar)
    planes, _ = construir_planes(red)
    corridas = correr_pareado(planes, ESCENARIOS, Parametros(replicas=5))
    assert len(corridas) == len(ESCENARIOS) * 5 * 2
    for i in range(0, len(vistos), 2):
        assert vistos[i] is vistos[i + 1]
    assert [c.politica for c in corridas[:2]] == ["actual", "algoritmo"]


def test_tablas(red):
    planes, _ = construir_planes(red)
    corridas = correr_pareado(planes, ESCENARIOS[:1], Parametros(replicas=3))
    filas = tabla_corridas(corridas)
    assert len(filas) == 6
    assert {"escenario", "politica", "replica", "espera_promedio", "utilizacion"} <= set(filas[0])
    resumen = tabla_resumen(corridas)
    assert [(f["politica"], f["replicas"]) for f in resumen] == [("actual", 3), ("algoritmo", 3)]
    assert "porcentaje_puntual_ic95" in resumen[0]


def test_barrido_monotono(red):
    planes, _ = construir_planes(red)
    corridas = barrido_vehiculos(planes, ESCENARIOS[2:], Parametros(replicas=2), range(4, 13))
    for politica in planes:
        for replica in range(2):
            esperas = [
                c.metricas.espera_promedio
                for c in corridas
                if c.politica == politica and c.replica == replica
            ]
            assert esperas == sorted(esperas, reverse=True)


@pytest.mark.parametrize(
    "kwargs", [{"replicas": 0}, {"replicas": 201}, {"vehiculos": 0}, {"limite_puntual": 0}, {"descarga": -1}]
)
def test_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        Parametros(**kwargs)
