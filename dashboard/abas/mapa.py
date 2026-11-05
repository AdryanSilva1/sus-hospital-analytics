import streamlit as st

from dashboard import visuais
from dashboard.componentes import aviso, grafico, tabela, tile, titulo
from dashboard.medidas import calcular, tirar_pequenos

TIPOS = ["Municípios pintados", "Bolhas", "Bolhas com ruas"]
EXPLICACAO = {
    "Municípios pintados": "Quanto mais escuro, maior a medida.",
    "Bolhas": "O tamanho da bolha é a medida escolhida; a cor é o estado.",
    "Bolhas com ruas": "O tamanho da bolha é a medida escolhida. O fundo precisa de internet.",
}


def por_municipio(painel):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "uf"], painel.medida)
    return tirar_pequenos(df, painel.medida)


def mapa(painel, df):
    malha = painel.tabelas["malha"]
    if malha is None:
        st.info("O mapa ainda não foi baixado. Rode `python -m pipeline.run` de novo.")
        return

    tipo = st.segmented_control("Tipo de mapa", TIPOS, default=TIPOS[0], key="tipo_mapa",
                                label_visibility="collapsed") or TIPOS[0]
    vista, escolhido = st.session_state.f_uf, st.session_state.cod_municipio

    if tipo == "Municípios pintados":
        fig = visuais.mapa_pintado(df, painel.medida, malha, vista, escolhido)
    else:
        fig = visuais.mapa(df, painel.medida, malha, vista, escolhido, com_ruas=tipo == "Bolhas com ruas")
    grafico(fig, "mapa", "cod_municipio", zoom=True)
    st.caption(f"{EXPLICACAO[tipo]} Rodinha do mouse dá zoom, arrastar move o mapa "
               "e duplo clique volta ao início.")


def mostrar(painel):
    df = por_municipio(painel)
    esq, dir_ = st.columns([1.5, 1])

    with esq, tile("mapa"):
        titulo(f"{painel.medida} por município (onde fica o hospital)")
        mapa(painel, df)
        aviso(painel, "municipio")

    with dir_, tile("ranking-mun"):
        titulo("Ranking de municípios")
        tabela(df, {"municipio": "Município", "uf": "UF"}, "ranking-mun", "cod_municipio",
               painel.medida, altura=640)
