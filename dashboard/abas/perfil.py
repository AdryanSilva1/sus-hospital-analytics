import streamlit as st

from dashboard import visuais
from dashboard.componentes import aviso, grafico, tile, titulo
from dashboard.medidas import calcular, tirar_pequenos

FAIXAS = ["0 a 14", "15 a 29", "30 a 44", "45 a 59", "60 a 74", "75 ou mais"]

GRUPOS = [
    ("faixa_etaria", "faixa etária", FAIXAS),
    ("sexo", "sexo", None),
    ("raca", "raça/cor", None),
]


def por_grupo(painel, coluna, ordem):
    df = calcular(painel.dados("perfil", ignorar=[coluna]), [coluna], painel.medida)
    df = tirar_pequenos(df, painel.medida)
    if ordem:
        presentes = set(df[coluna])
        df = df.set_index(coluna).reindex([o for o in ordem if o in presentes]).reset_index()

    fig = visuais.barras(df, coluna, painel.medida, coluna, st.session_state[coluna],
                         ordenar=ordem is None)
    grafico(fig, f"perfil-{coluna}", coluna)


def mostrar(painel):
    st.caption("Clique numa barra para ver só aquele grupo. Os números do topo e a "
               "Visão geral passam a mostrar só esse perfil.")

    for coluna_tela, (coluna, rotulo, ordem) in zip(st.columns(3), GRUPOS):
        with coluna_tela, tile(f"perfil-{coluna}"):
            titulo(f"{painel.medida} por {rotulo}")
            por_grupo(painel, coluna, ordem)
            aviso(painel, "perfil")
