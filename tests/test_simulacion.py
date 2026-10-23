import pytest

from logistica.metricas import Metricas, calcular_metricas, resumir
from logistica.pedidos import Pedido, generar_pedidos
from logistica.politicas import DESTINOS, TiemposRuta, plan_actual, tiempos
from logistica.simulacion import ConfigSim, simular

TIEMPOS = {"A": TiemposRuta(30, 20), "B": TiemposRuta(70, 10)}


def test_un_pedido_sin_espera():
    resultado = simular([Pedido(0, 5, "A")], TIEMPOS, ConfigSim(vehiculos=2, descarga=3))
    (registro,) = resultado.registros
    assert registro.espera == 0
    assert registro.entrega == 5 + 30 + 3
    assert registro.regreso == 5 + 30 + 3 + 20


def test_un_vehiculo_dos_pedidos_simultaneos():
    pedidos = [Pedido(0, 0, "A"), Pedido(1, 0, "A")]
    primero, segundo = simular(pedidos, TIEMPOS, ConfigSim(vehiculos=1)).registros
    assert primero.espera == 0
    assert segundo.espera == 50
    assert segundo.vehiculo == primero.vehiculo


def test_vehiculo_que_vuelve_atiende_pedido_del_mismo_instante():
    pedidos = [Pedido(0, 0, "A"), Pedido(1, 50, "A")]
    _, segundo = simular(pedidos, TIEMPOS, ConfigSim(vehiculos=1)).registros
    assert segundo.espera == 0


def test_fifo_con_cola():
    pedidos = [Pedido(i, float(i), "A") for i in range(6)]
    registros = simular(pedidos, TIEMPOS, ConfigSim(vehiculos=2)).registros
    inicios = [r.inicio for r in registros]
    assert inicios == sorted(inicios)


def test_metricas_a_mano():
    pedidos = [Pedido(0, 0, "A"), Pedido(1, 0, "B"), Pedido(2, 0, "A")]
    resultado = simular(pedidos, TIEMPOS, ConfigSim(vehiculos=2))
    # p0: 0-30-50, p1: 0-70-80, p2 espera hasta 50: 50-80-100 y llega tarde
    metricas = calcular_metricas(resultado, recepcion_min=60, limite_puntual=75)
    assert metricas == Metricas(
        pedidos=3,
        puntuales=2,
        porcentaje_puntual=pytest.approx(200 / 3),
        espera_promedio=pytest.approx(50 / 3),
        solicitud_entrega_promedio=pytest.approx((30 + 70 + 80) / 3),
        utilizacion=pytest.approx((50 + 80 + 50) / (2 * 100)),
        tiempo_extra=40,
        fin=100,
    )


def test_sin_pedidos():
    resultado = simular([], TIEMPOS, ConfigSim())
    assert calcular_metricas(resultado, 480) == Metricas(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_corrida_real_completa_y_determinista(red):
    pedidos = generar_pedidos(10, 8, DESTINOS, 11)
    plan = tiempos(plan_actual(red))
    resultado = simular(pedidos, plan, ConfigSim())
    assert len(resultado.registros) == len(pedidos)
    assert simular(pedidos, plan, ConfigSim()) == resultado
    metricas = calcular_metricas(resultado, 480)
    assert 0 <= metricas.utilizacion <= 1
    assert metricas.tiempo_extra >= 0


def test_destino_sin_ruta():
    with pytest.raises(ValueError):
        simular([Pedido(0, 0, "Z")], TIEMPOS, ConfigSim())


@pytest.mark.parametrize("kwargs", [{"vehiculos": 0}, {"vehiculos": 101}, {"vehiculos": 2.5}, {"descarga": -1}, {"descarga": 121}])
def test_config_invalida(kwargs):
    with pytest.raises(ValueError):
        ConfigSim(**kwargs)


def test_resumir():
    base = Metricas(1, 1, 100.0, 0.0, 10.0, 0.5, 0.0, 20.0)
    otra = Metricas(3, 1, 50.0, 4.0, 20.0, 0.7, 10.0, 30.0)
    resumen = resumir([base, otra])
    assert resumen["pedidos"].media == 2
    assert resumen["espera_promedio"].desviacion == pytest.approx(2 ** 1.5)
    assert resumen["pedidos"].ic95 == pytest.approx(1.96 * 2 ** 0.5 / 2 ** 0.5)
    assert resumir([base])["utilizacion"].ic95 == 0
    with pytest.raises(ValueError):
        resumir([])
