"""Quanto o SUS pagou pelas internações e como isso evolui no tempo."""

import streamlit as st

from dashboard import visuais
from dashboard.componentes import aviso, cartao, grafico, html, tabela_pbi, tile, titulo
from dashboard.medidas import calcular, formatar, porcentagem, tirar_pequenos, total
from dashboard.painel import MESES, NOMES_UF

GASTO = "Valor AIH"
ALTURA_FAIXA = 500  # os dois blocos de baixo com a mesma altura


def numeros(painel):
    base = painel.dados()
    soma = base[["valor_total", "dias_internado"]].sum()
    cirurgias = base.loc[base["tipo_procedimento"] == "Cirúrgico", "valor_total"].sum()
    por_dia = soma["valor_total"] / soma["dias_internado"] if soma["dias_internado"] else 0
    parte = cirurgias / soma["valor_total"] * 100 if soma["valor_total"] else 0

    with st.container(horizontal=True, key="cartoes-gastos"):
        cartao("💵 Gasto total com internações", formatar(soma["valor_total"], GASTO))
        cartao("🧾 Gasto médio por internação", formatar(total(base, "Valor Médio AIH"), GASTO))
        cartao("📅 Gasto por dia internado", formatar(por_dia, GASTO))
        cartao("🩺 Parte gasta em cirurgias", porcentagem(parte))


def mes_a_mes(painel):
    atual = calcular(painel.dados("mes"), ["mes"], GASTO)
    anterior = None
    if painel.ano - 1 in painel.anos:
        anterior = calcular(painel.dados("mes", ano=painel.ano - 1), ["mes"], GASTO)
    grafico(visuais.linha_mensal(atual, anterior, GASTO, painel.ano, MESES))
    aviso(painel, "mes")


def por_ano(painel):
    df = calcular(painel.dados(ignorar=["ano"]), ["ano"], GASTO).sort_values("ano")
    grafico(visuais.colunas(df, "ano", GASTO))
    if painel.anos[0] == painel.ano and painel.ultimo_mes < 12:
        st.caption(f"{painel.ano} ainda está incompleto (dados até {MESES[painel.ultimo_mes - 1]}).")


def por_coluna(painel, coluna, rotulo, nome, cor=visuais.AZUL, quantos=None):
    df = tirar_pequenos(calcular(painel.dados(ignorar=[coluna]), [coluna], GASTO), GASTO)
    if quantos:
        df = df.head(quantos)
    if coluna == "uf":
        df[rotulo] = df["uf"].map(NOMES_UF)
    grafico(visuais.barras(df, rotulo, GASTO, coluna, cor=cor), nome, coluna)


def top_municipios(painel):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "uf"], GASTO).head(15)
    grafico(visuais.barras(df, "municipio", GASTO, "cod_municipio", st.session_state.cod_municipio,
                           cor="uf"), "gasto-municipio", "cod_municipio")
    aviso(painel, "municipio")


def doencas_mais_caras(painel):
    medida = "Valor Médio AIH"
    df = calcular(painel.dados("cid", ignorar=["cid"]), ["cid", "descricao"], medida)
    linhas = tirar_pequenos(df, medida).head(40).to_dict("records")
    html(tabela_pbi(linhas, [("cid", "CID", "cid"), ("descricao", "Doença", "nome")], medida,
                    destaque=st.session_state.cid))
    aviso(painel, "cid")


def mostrar(painel):
    numeros(painel)

    with tile("gasto-mes"):
        titulo(f"Gasto mês a mês: {painel.ano} × {painel.ano - 1}")
        mes_a_mes(painel)

    esquerda, direita = st.columns(2)
    with esquerda:
        with tile("gasto-ano"):
            titulo("Gasto por ano")
            por_ano(painel)
        with tile("gasto-uf"):
            titulo("Gasto por estado")
            por_coluna(painel, "uf", "estado", "gasto-uf", cor="uf")
        with tile("gasto-proc"):
            titulo("Gasto por tipo de procedimento")
            por_coluna(painel, "tipo_procedimento", "tipo_procedimento", "gasto-proc")
    with direita, tile("gasto-sistema"):
        titulo("Gasto por sistema do corpo")
        por_coluna(painel, "capitulo_cid", "capitulo_cid", "gasto-sistema")

    esquerda, direita = st.columns(2)
    with esquerda, tile("gasto-mun", ALTURA_FAIXA):
        titulo("Municípios que mais receberam")
        top_municipios(painel)
    with direita, tile("gasto-cid", ALTURA_FAIXA):
        titulo("Doenças mais caras por internação (valor médio)")
        doencas_mais_caras(painel)
