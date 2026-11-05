"""Estado dos filtros do painel.

Todo clique num gráfico ou tabela passa por `definir()`. Clicar de novo no
mesmo item desmarca. Os filtros ficam no st.session_state.
"""

import streamlit as st

# Filtros que só existem em uma das tabelas resumidas
SO_MUNICIPIO = ["cod_municipio"]
SO_CID = ["cid"]
SO_PERFIL = ["sexo", "faixa_etaria", "raca"]

PADRAO = {
    "f_uf": "Sul",
    "f_proc": "Todos",
    "f_sistema": "Todos",
    "cod_municipio": None,
    "cid": None,
    "sexo": None,
    "faixa_etaria": None,
    "raca": None,
    "versao": 0,
}


def iniciar():
    for chave, valor in PADRAO.items():
        st.session_state.setdefault(chave, valor)


def chave(nome):
    """Key dos gráficos clicáveis. Muda a cada clique para a seleção não grudar."""
    return f"{nome}-{st.session_state.versao}"


def definir(coluna, valor):
    s = st.session_state

    if coluna == "uf":
        s.f_uf = "Sul" if s.f_uf == valor else valor
    elif coluna == "capitulo_cid":
        s.f_sistema = "Todos" if s.f_sistema == valor else valor
    elif coluna == "tipo_procedimento":
        s.f_proc = "Todos" if s.f_proc == valor else valor
    else:
        novo = None if s[coluna] == valor else valor
        # Município, CID e perfil vêm de tabelas diferentes, então
        # só dá para focar em um desses tipos por vez.
        if coluna in SO_MUNICIPIO:
            limpar(SO_CID + SO_PERFIL)
        elif coluna in SO_CID:
            limpar(SO_MUNICIPIO + SO_PERFIL)
        else:
            limpar(SO_MUNICIPIO + SO_CID)
        s[coluna] = novo

    s.versao += 1


def limpar(colunas=None):
    s = st.session_state
    for coluna in colunas or PADRAO:
        if coluna != "versao":
            s[coluna] = PADRAO[coluna]
    s.versao += 1


def ao_clicar_grafico(chave_widget, coluna):
    pontos = st.session_state[chave_widget]["selection"]["points"]
    for ponto in pontos:
        # Barras mandam o valor no customdata; no mapa vem o código em "location"
        valor = (ponto.get("customdata") or [ponto.get("location")])[0]
        if valor:
            definir(coluna, valor)
            return


def ao_clicar_tabela(chave_widget, coluna, valores):
    linhas = st.session_state[chave_widget]["selection"]["rows"]
    if linhas:
        definir(coluna, valores[linhas[0]])


def atuais(ano):
    """Filtros no formato coluna -> valor, prontos para o dados.recorte()."""
    s = st.session_state
    return {
        "uf": ["PR", "SC", "RS"] if s.f_uf == "Sul" else [s.f_uf],
        "ano": ano,
        "tipo_procedimento": s.f_proc,
        "capitulo_cid": s.f_sistema,
        "cod_municipio": s.cod_municipio,
        "cid": s.cid,
        "sexo": s.sexo,
        "faixa_etaria": s.faixa_etaria,
        "raca": s.raca,
    }
