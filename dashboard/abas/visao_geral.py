import streamlit as st

from dashboard import visuais
from dashboard.abas.comuns import por_estado, por_procedimento, por_sistema, top_municipios
from dashboard.componentes import aviso, grafico, tile, titulo
from dashboard.medidas import calcular
from dashboard.painel import MESES


def evolucao_mensal(painel):
    atual = calcular(painel.dados("mes"), ["mes"], painel.medida)
    anterior = None
    if painel.ano - 1 in painel.anos:
        anterior = calcular(painel.dados("mes", ano=painel.ano - 1), ["mes"], painel.medida)

    grafico(visuais.linha_mensal(atual, anterior, painel.medida, painel.ano, MESES))
    aviso(painel, "mes")


def mostrar(painel):
    with tile("geral-mes"):
        titulo(f"{painel.medida} mês a mês: {painel.ano} × {painel.ano - 1}")
        evolucao_mensal(painel)

    esq, meio, dir_ = st.columns([1, 1.2, 1])
    with esq:
        with tile("geral-uf"):
            titulo(f"{painel.medida} por estado")
            por_estado(painel, painel.medida, "geral-uf")
        with tile("geral-proc"):
            titulo(f"{painel.medida} por tipo de procedimento")
            por_procedimento(painel, painel.medida, "geral-proc")
    with meio, tile("geral-sistema"):
        titulo(f"{painel.medida} por sistema do corpo")
        por_sistema(painel, painel.medida, "geral-sistema")
    with dir_, tile("geral-mun"):
        titulo(f"Top 15 municípios · {painel.medida}")
        top_municipios(painel, painel.medida, "geral-mun")
