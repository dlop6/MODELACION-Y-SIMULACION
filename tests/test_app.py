from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "src" / "logistica" / "app.py"


def _por_etiqueta(widgets, etiqueta):
    return next(w for w in widgets if w.label == etiqueta)


@pytest.fixture
def app() -> AppTest:
    prueba = AppTest.from_file(str(APP), default_timeout=120)
    prueba.run()
    assert not prueba.exception
    return prueba


def test_carga_con_cuatro_pestanas(app):
    assert [t.label for t in app.tabs] == ["red", "rutas", "simulación", "experimentos"]
    assert not app.warning


def test_escenario_precarga_la_tasa(app):
    _por_etiqueta(app.selectbox, "escenario").set_value("navidad").run()
    assert not app.exception
    assert app.session_state.tasa == 10


def test_cerrar_tramo_de_la_ruta_actual(app):
    _por_etiqueta(app.selectbox, "origen del tramo").set_value("N07").run()
    _por_etiqueta(app.selectbox, "destino del tramo").set_value("N08")
    _por_etiqueta(app.radio, "acción").set_value("cerrar tramo")
    _por_etiqueta(app.button, "aplicar").click().run()
    assert not app.exception
    assert app.session_state.incidentes[0].describir() == "N07->N08 cerrado"
    assert any("N07->N08" in w.value for w in app.warning)
    _por_etiqueta(app.button, "quitar todos los incidentes").click().run()
    assert app.session_state.incidentes == []
    assert not app.warning


def test_cambiar_tiempo_de_un_tramo(app):
    _por_etiqueta(app.selectbox, "destino del tramo").set_value("N02")
    _por_etiqueta(app.number_input, "nuevo tiempo (min)").set_value(30.0)
    _por_etiqueta(app.button, "aplicar").click().run()
    assert not app.exception
    assert app.session_state.incidentes[0].describir() == "N01->N02 30 min"


def test_correr_experimentos(app):
    _por_etiqueta(app.number_input, "réplicas (experimentos)").set_value(2).run()
    _por_etiqueta(app.slider, "barrido de vehículos").set_value((7, 8)).run()
    _por_etiqueta(app.button, "correr experimentos").click().run()
    assert not app.exception
    assert "experimento" in app.session_state
    assert len(app.session_state.experimento["resumen"]) == 6
