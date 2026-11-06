"""Quanto o SUS pagou pelas internações e como isso evolui no tempo."""

import streamlit as st

from dashboard import visuais
from dashboard.brasil import ESTADOS
from dashboard.componentes import aviso, cartao, grafico, html, tabela_pbi, tile, titulo
from dashboard.medidas import calcular, formatar, porcentagem, tirar_pequenos, total, variacao
from dashboard.painel import MESES

GASTO = "Valor AIH"
# Altura das faixas de blocos (px): blocos lado a lado com a mesma altura
ALTURA_FAIXA_1 = 255
ALTURA_FAIXA_2 = 620


def _gasto_por_dia(df):
    dias = df["dias_internado"].sum()
    return df["valor_total"].sum() / dias if dias else 0


def _comparar(atual, anterior):
    mudanca = variacao(atual, anterior)
    return f"{mudanca} vs mesmo período do ano anterior" if mudanca else None


def numeros(painel):
    base = painel.dados()
    gasto_total = base["valor_total"].sum()
    cirurgias = base.loc[base["tipo_procedimento"] == "Cirúrgico", "valor_total"].sum()
    parte = cirurgias / gasto_total * 100 if gasto_total else 0

    detalhes = [None, None, None]
    comparacao = painel.mesmo_periodo_do_ano_anterior()
    if comparacao:
        atual, anterior = comparacao
        detalhes = [
            _comparar(atual["valor_total"].sum(), anterior["valor_total"].sum()),
            _comparar(total(atual, "Valor Médio AIH"), total(anterior, "Valor Médio AIH")),
            _comparar(_gasto_por_dia(atual), _gasto_por_dia(anterior)),
        ]

    with st.container(horizontal=True, key="cartoes-gastos"):
        cartao("gasto", "Gasto total com internações", formatar(gasto_total, GASTO), detalhes[0])
        cartao("recibo", "Gasto médio por internação", formatar(total(base, "Valor Médio AIH"), GASTO),
               detalhes[1])
        cartao("calendario", "Gasto por dia internado", formatar(_gasto_por_dia(base), GASTO), detalhes[2])
        cartao("cirurgia", "Parte gasta em cirurgias", porcentagem(parte),
               f"{formatar(cirurgias, GASTO)} em cirurgias")


def mes_a_mes(painel):
    atual = calcular(painel.dados("mes"), ["mes"], GASTO)
    anterior = None
    if painel.ano - 1 in painel.anos:
        anterior = calcular(painel.dados("mes", ano=painel.ano - 1), ["mes"], GASTO)
    grafico(visuais.linha_mensal(atual, anterior, GASTO, painel.ano, MESES))
    aviso(painel, "mes")


def por_ano(painel):
    df = calcular(painel.dados(ignorar=["ano"]), ["ano"], GASTO).sort_values("ano")
    grafico(visuais.colunas(df, "ano", GASTO, destaque=painel.ano, altura=165))
    if painel.anos[0] == painel.ano and painel.ultimo_mes < 12:
        st.caption(f"{painel.ano} ainda está incompleto (dados até {MESES[painel.ultimo_mes - 1]}).")


def por_coluna(painel, coluna, rotulo, nome, quantos=None):
    df = tirar_pequenos(calcular(painel.dados(ignorar=[coluna]), [coluna], GASTO), GASTO)
    if quantos:
        df = df.head(quantos)
    if coluna == "uf":
        df[rotulo] = df["uf"].map(ESTADOS)
    cor = "uf" if coluna == "uf" else None
    grafico(visuais.barras(df, rotulo, GASTO, coluna, cor=cor), nome, coluna)


def top_municipios(painel):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "uf"], GASTO).head(15)
    grafico(visuais.barras(df, "municipio", GASTO, "cod_municipio", st.session_state.cod_municipio,
                           cor="uf"),
            "gasto-municipio", "cod_municipio")
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

    # Duas faixas de três blocos com a mesma altura, para não sobrar buraco
    ano, estado, procedimento = st.columns(3)
    with ano, tile("gasto-ano", ALTURA_FAIXA_1):
        titulo("Gasto por ano")
        por_ano(painel)
    with estado, tile("gasto-uf", ALTURA_FAIXA_1):
        titulo("Gasto por estado")
        por_coluna(painel, "uf", "estado", "gasto-uf")
    with procedimento, tile("gasto-proc", ALTURA_FAIXA_1):
        titulo("Gasto por tipo de procedimento")
        por_coluna(painel, "tipo_procedimento", "tipo_procedimento", "gasto-proc")

    sistema, municipio, doenca = st.columns([1, 1, 1.25])
    with sistema, tile("gasto-sistema", ALTURA_FAIXA_2):
        titulo("Gasto por sistema do corpo")
        por_coluna(painel, "capitulo_cid", "capitulo_cid", "gasto-sistema")
    with municipio, tile("gasto-mun", ALTURA_FAIXA_2):
        titulo("Municípios que mais receberam")
        top_municipios(painel)
    with doenca, tile("gasto-cid", ALTURA_FAIXA_2):
        titulo("Doenças mais caras por internação (valor médio)")
        doencas_mais_caras(painel)
