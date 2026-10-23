import pytest

from logistica.comparacion import comparar_rutas, es_puntual_sin_espera
from logistica.politicas import DESTINOS, PlanInvalido, TiemposRuta, plan_actual, plan_optimo, tiempos


def test_plan_actual(red):
    plan = tiempos(plan_actual(red))
    assert plan == {
        "N08": TiemposRuta(59, 59),
        "N19": TiemposRuta(33, 33),
        "N34": TiemposRuta(42, 42),
        "N40": TiemposRuta(93, 93),
    }


def test_plan_optimo(red):
    plan = tiempos(plan_optimo(red))
    assert {d: (t.ida, t.regreso, t.ciclo) for d, t in plan.items()} == {
        "N08": (51, 59, 110),
        "N19": (18, 24, 42),
        "N34": (24, 34, 58),
        "N40": (47, 61, 108),
    }


def test_cerrar_tramo_de_ruta_actual(red):
    cerrada = red.sin_arco("N07", "N08")
    with pytest.raises(PlanInvalido) as error:
        plan_actual(cerrada)
    assert error.value.tramo == ("N07", "N08")
    assert set(plan_optimo(cerrada)) == set(DESTINOS)


def test_destino_inalcanzable(red):
    aislada = red.sin_arco("N32", "N40").sin_arco("N39", "N40")
    with pytest.raises(PlanInvalido) as error:
        plan_optimo(aislada)
    assert error.value.destino == "N40"
    assert error.value.sentido == "ida"


def test_tabla_comparativa(red):
    filas = comparar_rutas(red, k=3)
    for destino in DESTINOS:
        propias = [f for f in filas if f.destino == destino]
        assert [f.opcion for f in propias] == ["actual", "algoritmo", "alternativa 1", "alternativa 2"]
        assert all(f.valida and red.es_valida(f.ida.nodos) and red.es_valida(f.regreso.nodos) for f in propias)
        actual, algoritmo = propias[0], propias[1]
        assert algoritmo.ciclo <= actual.ciclo
    n40 = next(f for f in filas if f.destino == "N40" and f.opcion == "actual")
    assert es_puntual_sin_espera(n40) is False
    assert es_puntual_sin_espera(n40, limite=100) is True


def test_tabla_con_ruta_actual_cerrada(red):
    filas = comparar_rutas(red.sin_arco("N07", "N08"))
    actual = next(f for f in filas if f.destino == "N08" and f.opcion == "actual")
    assert not actual.valida
    assert actual.ciclo is None
    assert "N07->N08" in actual.nota
    assert es_puntual_sin_espera(actual) is None
