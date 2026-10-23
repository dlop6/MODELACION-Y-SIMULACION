import pytest

from logistica.red import Red, RedInvalida, RutaInvalida, cargar_red

RUTAS_DECLARADAS = {
    "N08": ("N01 N02 N03 N04 N05 N06 N07 N08", 59),
    "N19": ("N01 N02 N03 N11 N19", 33),
    "N34": ("N01 N09 N17 N25 N33 N34", 42),
    "N40": ("N01 N02 N03 N04 N05 N06 N07 N08 N16 N24 N32 N40", 93),
}


def _escribir(tmp_path, contenido):
    ruta = tmp_path / "m.csv"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_tamano_de_la_red(red):
    assert len(red.nodos) == 40
    assert len(red.lista_arcos()) == 144


def test_sentidos_y_asimetrias(red):
    arcos = red.lista_arcos()
    un_sentido = [(o, d) for o, d, _ in arcos if red.tiempo(d, o) is None]
    pesos_distintos = [
        (o, d) for o, d, t in arcos if o < d and red.tiempo(d, o) not in (None, t)
    ]
    assert len(un_sentido) == 18
    assert ("N01", "N17") in un_sentido
    assert len(pesos_distintos) == 14


@pytest.mark.parametrize("destino", RUTAS_DECLARADAS)
def test_rutas_actuales_validas_ida_y_regreso(red, destino):
    texto, minutos = RUTAS_DECLARADAS[destino]
    ida = texto.split()
    assert red.costo(ida) == minutos
    assert red.costo(ida[::-1]) == minutos


def test_tramo_inexistente_indica_cual(red):
    with pytest.raises(RutaInvalida) as error:
        red.costo(["N01", "N08"])
    assert error.value.tramo == ("N01", "N08")
    assert not red.es_valida(["N01", "N08"])
    assert not red.es_valida(["N01"])


def test_cambios_no_mutan_la_original(red):
    cerrada = red.sin_arco("N01", "N02")
    lenta = red.con_tiempo("N01", "N02", 20)
    assert red.tiempo("N01", "N02") == 8
    assert cerrada.tiempo("N01", "N02") is None
    assert lenta.tiempo("N01", "N02") == 20
    with pytest.raises(TypeError):
        red.arcos["N01"]["N02"] = 1


@pytest.mark.parametrize("tiempo", [0, -3, float("inf"), float("nan"), 501])
def test_tiempo_fuera_de_rango(red, tiempo):
    with pytest.raises(RedInvalida):
        red.con_tiempo("N01", "N02", tiempo)


def test_cambio_sobre_arco_inexistente(red):
    with pytest.raises(RedInvalida):
        red.sin_arco("N01", "N08")


def test_red_rechaza_nodos_desconocidos():
    with pytest.raises(RedInvalida):
        Red(("N01",), {"N01": {"N99": 3}})


@pytest.mark.parametrize(
    "contenido",
    [
        "x,N01,N02\nN01,0,5\n",
        "x,N01,N02\nN01,0,-5\nN02,5,0\n",
        "x,N01,N02\nN01,0,abc\nN02,5,0\n",
        "x,N01,N02\nN02,0,5\nN01,5,0\n",
        "x,N01,N02\nN01,3,5\nN02,5,0\n",
        "x,A1,N02\nA1,0,5\nN02,5,0\n",
        "x,N01,N02\nN01,0\nN02,5,0\n",
    ],
    ids=["no_cuadrada", "negativo", "texto", "orden", "diagonal", "nombre", "columnas"],
)
def test_csv_corrupto(tmp_path, contenido):
    with pytest.raises(RedInvalida):
        cargar_red(_escribir(tmp_path, contenido))


def test_csv_con_guion_es_sin_conexion(tmp_path):
    red = cargar_red(_escribir(tmp_path, "x,N01,N02\nN01,0,—\nN02,4,0\n"))
    assert red.lista_arcos() == [("N02", "N01", 4.0)]


def test_archivo_inexistente(tmp_path):
    with pytest.raises(RedInvalida):
        cargar_red(tmp_path / "no.csv")
