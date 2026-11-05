"""Gráficos que aparecem em mais de uma aba (com a medida escolhida ou com o gasto)."""

import streamlit as st

from dashboard import visuais
from dashboard.componentes import aviso, grafico
from dashboard.medidas import calcular, tirar_pequenos
from dashboard.painel import NOMES_UF


def por_estado(painel, medida, nome):
    df = calcular(painel.dados(ignorar=["uf"]), ["uf"], medida)
    df["nome"] = df["uf"].map(NOMES_UF)
    escolhido = st.session_state.f_uf if st.session_state.f_uf != "Sul" else None
    grafico(visuais.barras(df, "nome", medida, "uf", escolhido, cor="uf", altura=130), nome, "uf")


def por_sistema(painel, medida, nome):
    df = calcular(painel.dados(ignorar=["capitulo_cid"]), ["capitulo_cid"], medida)
    escolhido = st.session_state.f_sistema if st.session_state.f_sistema != "Todos" else None
    grafico(visuais.barras(tirar_pequenos(df, medida), "capitulo_cid", medida, "capitulo_cid",
                           escolhido), nome, "capitulo_cid")


def por_procedimento(painel, medida, nome):
    df = calcular(painel.dados(ignorar=["tipo_procedimento"]), ["tipo_procedimento"], medida)
    escolhido = st.session_state.f_proc if st.session_state.f_proc != "Todos" else None
    grafico(visuais.barras(df, "tipo_procedimento", medida, "tipo_procedimento", escolhido,
                           altura=110), nome, "tipo_procedimento")


def top_municipios(painel, medida, nome, quantos=15):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "uf"], medida)
    df = tirar_pequenos(df, medida).head(quantos)
    grafico(visuais.barras(df, "municipio", medida, "cod_municipio",
                           st.session_state.cod_municipio, cor="uf"), nome, "cod_municipio")
    aviso(painel, "municipio")
