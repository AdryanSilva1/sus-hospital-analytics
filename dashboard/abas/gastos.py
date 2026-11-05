import streamlit as st

from dashboard import visuais
from dashboard.abas.comuns import por_estado, por_procedimento, por_sistema, top_municipios
from dashboard.componentes import aviso, cartao, grafico, tabela, tile, titulo
from dashboard.medidas import calcular, formatar, porcentagem, tirar_pequenos, total
from dashboard.painel import MESES

GASTO = "Valor AIH"


def numeros(painel):
    base = painel.dados()
    soma = base[["valor_total", "dias_internado"]].sum()
    cirurgias = base.loc[base["tipo_procedimento"] == "Cirúrgico", "valor_total"].sum()

    with st.container(horizontal=True, key="cartoes-gastos"):
        cartao("Gasto total com internações", formatar(soma["valor_total"], GASTO))
        cartao("Gasto médio por internação", formatar(total(base, "Valor Médio AIH"), GASTO))
        por_dia = soma["valor_total"] / soma["dias_internado"] if soma["dias_internado"] else 0
        cartao("Gasto por dia internado", formatar(por_dia, GASTO))
        parte = cirurgias / soma["valor_total"] * 100 if soma["valor_total"] else 0
        cartao("Parte gasta em cirurgias", porcentagem(parte))


def por_ano(painel):
    df = calcular(painel.dados(ignorar=["ano"]), ["ano"], GASTO).sort_values("ano")
    grafico(visuais.colunas(df, "ano", GASTO))

    mais_recente = painel.anos[0]
    if mais_recente == painel.ano and painel.ultimo_mes < 12:
        st.caption(f"{mais_recente} ainda está incompleto (dados até {MESES[painel.ultimo_mes - 1]}).")


def doencas_mais_caras(painel):
    medida = "Valor Médio AIH"
    df = calcular(painel.dados("cid", ignorar=["cid"]), ["cid", "descricao"], medida)
    df = tirar_pequenos(df, medida).head(40)
    tabela(df, {"cid": "CID", "descricao": "Doença"}, "gasto-cid", "cid", medida, altura=470)
    aviso(painel, "cid")


def mostrar(painel):
    numeros(painel)

    esq, dir_ = st.columns(2)
    with esq:
        with tile("gasto-ano"):
            titulo("Gasto por ano")
            por_ano(painel)
        with tile("gasto-uf"):
            titulo("Gasto por estado")
            por_estado(painel, GASTO, "gasto-uf")
        with tile("gasto-proc"):
            titulo("Gasto por tipo de procedimento")
            por_procedimento(painel, GASTO, "gasto-proc")
    with dir_, tile("gasto-sistema"):
        titulo("Gasto por sistema do corpo")
        por_sistema(painel, GASTO, "gasto-sistema")

    esq, dir_ = st.columns(2)
    with esq, tile("gasto-mun"):
        titulo("Municípios que mais gastaram")
        top_municipios(painel, GASTO, "gasto-mun")
    with dir_, tile("gasto-cid"):
        titulo("Doenças mais caras por internação (valor médio)")
        doencas_mais_caras(painel)
