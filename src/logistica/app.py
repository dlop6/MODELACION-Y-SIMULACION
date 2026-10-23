"""app de streamlit para estudiar rutas, flota e incidentes viales."""

from __future__ import annotations

import sys
from pathlib import Path

# streamlit corre este archivo como script suelto, así que se agrega src/ a mano
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from logistica.comparacion import LIMITE_PUNTUAL_MIN, comparar_rutas, tabla_rutas
from logistica.escenarios import ESCENARIOS, Escenario
from logistica.experimentos import (
    REPLICAS_MAXIMAS,
    Parametros,
    barrido_vehiculos,
    construir_planes,
    correr_pareado,
    simular_politicas,
    tabla_corridas,
    tabla_resumen,
)
from logistica.exportar import filas_a_csv
from logistica.graficas import fig_barrido, fig_metricas, fig_red
from logistica.metricas import ETIQUETAS, INDICADORES_CLAVE
from logistica.pedidos import DURACION_MAXIMA_H, DURACION_MINIMA_H, TASA_MAXIMA, generar_pedidos
from logistica.politicas import DESTINOS, PlanInvalido, plan_actual, plan_optimo
from logistica.red import TIEMPO_MAXIMO_TRAMO, Incidente, Red, RedInvalida, aplicar_incidentes, cargar_red
from logistica.simulacion import DESCARGA_MAXIMA, VEHICULOS_MAXIMOS

_PRESETS = {e.nombre: e.pedidos_por_hora for e in ESCENARIOS}


@st.cache_resource
def red_base() -> Red:
    return cargar_red()


def _aplicar_escenario() -> None:
    st.session_state.tasa = _PRESETS[st.session_state.escenario]


def barra_lateral() -> Parametros:
    st.sidebar.header("parámetros")
    st.session_state.setdefault("tasa", _PRESETS["normal"])
    st.sidebar.selectbox("escenario", list(_PRESETS), key="escenario", on_change=_aplicar_escenario)
    st.sidebar.number_input("pedidos por hora", 0.5, TASA_MAXIMA, step=0.5, key="tasa")
    parametros = Parametros(
        duracion_h=st.sidebar.number_input("recepción (h)", DURACION_MINIMA_H, DURACION_MAXIMA_H, 8.0, 0.5),
        vehiculos=st.sidebar.number_input("vehículos", 1, VEHICULOS_MAXIMOS, 8),
        descarga=st.sidebar.number_input("descarga en destino (min)", 0.0, DESCARGA_MAXIMA, 0.0, 1.0),
        limite_puntual=st.sidebar.number_input("límite de puntualidad (min)", 1.0, 1440.0, LIMITE_PUNTUAL_MIN, 5.0),
        replicas=st.sidebar.number_input("réplicas (experimentos)", 1, REPLICAS_MAXIMAS, 30),
        semilla_base=st.sidebar.number_input("semilla", 0, 2**31 - 1, 1),
    )
    return parametros


def pestana_red(base: Red, red: Red) -> None:
    st.subheader("incidentes viales")
    st.caption(
        "cada cambio arma una red nueva a partir de la original y dijkstra recalcula las rutas óptimas; "
        "la ruta actual se mantiene y, si usa un tramo cerrado, queda inválida."
    )
    origen = st.selectbox("origen del tramo", red.nodos)
    destinos = sorted(red.arcos[origen])
    with st.form("incidente"):
        destino = st.selectbox("destino del tramo", destinos)
        accion = st.radio("acción", ["cambiar tiempo", "cerrar tramo"], horizontal=True)
        actual = red.tiempo(origen, destino) if destino else 1.0
        tiempo = st.number_input("nuevo tiempo (min)", 0.5, TIEMPO_MAXIMO_TRAMO, float(actual), 0.5)
        if st.form_submit_button("aplicar", disabled=not destinos):
            nuevo = Incidente(origen, destino, None if accion == "cerrar tramo" else tiempo)
            try:
                aplicar_incidentes(base, [*st.session_state.incidentes, nuevo])
            except RedInvalida as error:
                st.error(str(error))
            else:
                st.session_state.incidentes.append(nuevo)
                st.rerun()

    if st.session_state.incidentes:
        st.write("activos: " + "; ".join(i.describir() for i in st.session_state.incidentes))
        if st.button("quitar todos los incidentes"):
            st.session_state.incidentes = []
            st.rerun()

    st.subheader("grafo")
    foco = st.selectbox("resaltar rutas hacia", ["ninguno", *DESTINOS])
    st.pyplot(fig_red(red, _rutas_a_resaltar(red, foco)))


def _rutas_a_resaltar(red: Red, destino: str) -> dict[str, tuple[str, ...]]:
    if destino == "ninguno":
        return {}
    resaltar = {}
    for etiqueta, planificar in (("actual", plan_actual), ("algoritmo", plan_optimo)):
        try:
            rutas = planificar(red)[destino]
        except PlanInvalido:
            continue
        resaltar[f"{etiqueta} ida"] = rutas.ida.nodos
        resaltar[f"{etiqueta} regreso"] = rutas.regreso.nodos
    return resaltar


def _avisos(errores: dict[str, str]) -> None:
    for politica, error in errores.items():
        st.warning(f"la política «{politica}» no se puede aplicar: {error}")


def pestana_rutas(red: Red, parametros: Parametros, errores: dict[str, str]) -> None:
    _avisos(errores)
    k = st.slider("rutas por destino y sentido (yen)", 2, 10, 3)
    filas = tabla_rutas(comparar_rutas(red, k), parametros.descarga, parametros.limite_puntual)
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


def pestana_simulacion(planes, parametros: Parametros, errores: dict[str, str]) -> None:
    _avisos(errores)
    if not planes:
        st.error("no hay políticas válidas para simular")
        return
    tasa = st.session_state.tasa
    pedidos = generar_pedidos(tasa, parametros.duracion_h, DESTINOS, parametros.semilla_base)
    st.write(f"{len(pedidos)} pedidos con {tasa:g} pedidos/h y semilla {parametros.semilla_base}")
    resultados = simular_politicas(planes, pedidos, parametros)
    for columna, (politica, (resultado, metricas)) in zip(st.columns(len(resultados)), resultados.items()):
        with columna:
            st.markdown(f"**{politica}**")
            for indicador in INDICADORES_CLAVE:
                valor = getattr(metricas, indicador)
                st.metric(ETIQUETAS[indicador], f"{valor:.2f}" if indicador == "utilizacion" else f"{valor:.1f}")
            st.caption(f"{metricas.puntuales} de {metricas.pedidos} entregas puntuales")
            registros = [
                {
                    "pedido": r.pedido.id,
                    "destino": r.pedido.destino,
                    "llegada": r.pedido.llegada,
                    "vehiculo": r.vehiculo,
                    "espera": r.espera,
                    "entrega": r.entrega,
                    "regreso": r.regreso,
                    "puntual": r.solicitud_entrega <= parametros.limite_puntual,
                }
                for r in resultado.registros
            ]
            st.dataframe(pd.DataFrame(registros).round(1), hide_index=True, height=300)


def pestana_experimentos(planes, parametros: Parametros, errores: dict[str, str]) -> None:
    _avisos(errores)
    flotas = st.slider("barrido de vehículos", 1, VEHICULOS_MAXIMOS, (4, 20))
    escenarios = list(ESCENARIOS)
    if st.session_state.tasa not in _PRESETS.values():
        escenarios.append(Escenario(f"personalizado ({st.session_state.tasa:g}/h)", st.session_state.tasa))
    firma = (tuple(planes.items()), parametros, flotas, tuple(escenarios))
    if st.button("correr experimentos", disabled=not planes):
        corridas = correr_pareado(planes, escenarios, parametros)
        barrido = barrido_vehiculos(planes, escenarios, parametros, range(flotas[0], flotas[1] + 1))
        st.session_state.experimento = {
            "firma": firma,
            "replicas": tabla_corridas(corridas),
            "resumen": tabla_resumen(corridas),
            "barrido": tabla_resumen(barrido),
        }
    datos = st.session_state.get("experimento")
    if not datos:
        st.info("ajustá los parámetros y presioná «correr experimentos»")
        return
    if datos["firma"] != firma:
        st.warning("los parámetros cambiaron; estos resultados son de la corrida anterior")
    st.dataframe(pd.DataFrame(datos["resumen"]).round(2), hide_index=True, width="stretch")
    indicador = st.selectbox("indicador", INDICADORES_CLAVE, format_func=ETIQUETAS.get)
    st.pyplot(fig_metricas(datos["resumen"], indicador))
    st.pyplot(fig_barrido(datos["barrido"], indicador))
    for nombre in ("replicas", "resumen", "barrido"):
        st.download_button(f"descargar {nombre}.csv", filas_a_csv(datos[nombre]), f"{nombre}.csv", "text/csv")


def main() -> None:
    st.set_page_config(page_title="logística del valle", layout="wide")
    st.title("logística del valle · rutas y flota")
    st.session_state.setdefault("incidentes", [])
    parametros = barra_lateral()
    base = red_base()
    red = aplicar_incidentes(base, st.session_state.incidentes)
    planes, errores = construir_planes(red)
    red_tab, rutas_tab, sim_tab, exp_tab = st.tabs(["red", "rutas", "simulación", "experimentos"])
    with red_tab:
        pestana_red(base, red)
    with rutas_tab:
        pestana_rutas(red, parametros, errores)
    with sim_tab:
        pestana_simulacion(planes, parametros, errores)
    with exp_tab:
        pestana_experimentos(planes, parametros, errores)


main()
