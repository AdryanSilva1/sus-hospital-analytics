# =============================================================
# app.py — SUS Sul Analytics
#
# Como rodar:
#   pip install -r requirements.txt
#   python -m streamlit run app.py
# =============================================================

from datetime import date
from pathlib import Path

import streamlit as st

from dashboard import visuais
from dashboard.dados import (ICONES_MEDIDA, ICONES_SISTEMA, MEDIDAS, MINIMO_PARA_RAZAO,
                             SISTEMAS_BOTOES, calcular, carregar, eh_razao, filtrar,
                             formatar, total)
from dashboard.layout import LOGO, html, tile, titulo

NOMES_UF = {"Sul": "Região Sul", "PR": "Paraná", "SC": "Santa Catarina", "RS": "Rio Grande do Sul"}


# ── Configuração ─────────────────────────────────────────────
st.set_page_config(page_title="SUS Sul Analytics", page_icon="🏥", layout="wide")

css = Path(__file__).parent / "dashboard" / "styles.css"
html(f"<style>{css.read_text(encoding='utf-8')}</style>")


# ── Dados ────────────────────────────────────────────────────
try:
    tabelas, controle = carregar()
except FileNotFoundError:
    st.info("Ainda não há dados. Rode primeiro: `python -m pipeline.run`")
    st.stop()

anos = sorted(controle["ano"].unique(), reverse=True)
ultimo = controle.sort_values(["ano", "ultimo_mes"]).iloc[-1]
atualizado = date.fromisoformat(controle["atualizado_em"].max())


# ── Linha 1: cabeçalho em blocos ─────────────────────────────
c_logo, c_titulo, c_uf, c_kpi, c_ano, c_ajuda, c_atual = st.columns(
    [0.55, 2.3, 1.45, 1.6, 0.85, 0.45, 1.5], vertical_alignment="center"
)

with c_logo, tile("logo"):
    html(f'<div class="logo">{LOGO}</div>')

with c_titulo, tile("titulo"):
    estado_placeholder = st.empty()

with c_uf, tile("uf"):
    uf = st.segmented_control("Estado", ["Sul", "PR", "SC", "RS"], default="Sul",
                              label_visibility="collapsed") or "Sul"

with c_ano, tile("ano"):
    ano = st.selectbox("Ano", anos, label_visibility="collapsed")

with c_ajuda, tile("ajuda"):
    with st.popover("?"):
        st.markdown(f"""
**Como usar**
- Escolha o estado e o ano no topo.
- Clique num sistema do corpo para filtrar o painel inteiro.
- Na direita, escolha a medida (internações, óbitos, valor...).

**Fonte**: SIH/SUS — DATASUS, Ministério da Saúde. Nomes dos municípios: IBGE.

**Regras**
- Internação = AIH principal aprovada.
- Município = onde fica o hospital.
- Valores em R$ sem correção pela inflação.
- Em medidas de média e porcentagem, municípios e CIDs com menos de
  {MINIMO_PARA_RAZAO} internações ficam fora dos rankings.

**Não está aqui**: fila de espera e mortes na fila (não há base pública nacional).
""")

with c_atual, tile("atualizado"):
    html(f"""
        <div class="atualizado">
            <div class="atualizado-icone">🗓️</div>
            <div>
                <div class="atualizado-rotulo">Dados até {int(ultimo.ultimo_mes):02d}/{int(ultimo.ano)}</div>
                <div class="atualizado-data">Atualizado em {atualizado:%d/%m/%Y}</div>
            </div>
        </div>""")

estado_placeholder.markdown(f"""
    <div class="titulo-painel">Informações Hospitalares (SUS/SIH)</div>
    <div class="subtitulo-painel">{NOMES_UF[uf]}</div>""", unsafe_allow_html=True)


# ── Linha 2: sistemas do corpo ───────────────────────────────
with tile("sistemas"):
    opcoes = {f"{ICONES_SISTEMA[s]}  {s}": s for s in SISTEMAS_BOTOES}
    escolhido = st.pills("Sistema", list(opcoes), label_visibility="collapsed")
    sistema = opcoes.get(escolhido)


# ── Linha 3: visuais ─────────────────────────────────────────
col_esq, col_meio, col_dir = st.columns([1.05, 1.5, 1.0])

# A coluna da direita vem primeiro no código porque os filtros dela
# mudam os visuais das outras colunas.
with col_dir:
    with tile("filtros"):
        faixa = st.selectbox("Faixa Etária", ["Todos", "0 a 14", "15 a 29", "30 a 44",
                                              "45 a 59", "60 a 74", "75 ou mais"])
        raca = st.selectbox("Raça/Cor", ["Todos", "Branca", "Preta", "Parda", "Amarela",
                                         "Indígena", "Sem informação"])
        sexo = st.selectbox("Sexo", ["Todos", "Feminino", "Masculino"])
        procedimento = st.selectbox("Procedimento", ["Todos", "Cirúrgico", "Clínico"])

    with tile("medidas"):
        medida = st.radio(
            "Medida", list(MEDIDAS), label_visibility="collapsed",
            format_func=lambda m: f"{ICONES_MEDIDA[m]}  {m}",
        )

ufs = ["PR", "SC", "RS"] if uf == "Sul" else [uf]
base = dict(uf=ufs, ano=int(ano), tipo_procedimento=procedimento)
perfil_paciente = dict(faixa_etaria=faixa, raca=raca, sexo=sexo)

mun = filtrar(tabelas["municipio"], **base, capitulo_cid=sistema)
cid = filtrar(tabelas["cid"], **base, capitulo_cid=sistema)
perfil = filtrar(tabelas["perfil"], **base, **perfil_paciente)
perfil_sistema = filtrar(perfil, capitulo_cid=sistema)


def tirar_pequenos(df):
    if eh_razao(medida):
        return df[df["internacoes"] >= MINIMO_PARA_RAZAO]
    return df


# KPI do topo (depende da medida, por isso é desenhado agora)
with c_kpi, tile("kpi"):
    html(f"""
        <div class="kpi">
            <div class="kpi-icone">{ICONES_MEDIDA[medida]}</div>
            <div>
                <div class="kpi-rotulo">{medida}</div>
                <div class="kpi-valor">{formatar(total(perfil_sistema, medida), medida)}</div>
            </div>
        </div>""")


with col_esq:
    with tile("por-estado"):
        titulo(f"{medida} por estado", ICONES_MEDIDA[medida])
        por_uf = calcular(mun, ["uf"], medida)
        por_uf["nome"] = por_uf["uf"].map(NOMES_UF)
        st.plotly_chart(visuais.barras(por_uf, "nome", medida, altura=150),
                        width="stretch", config=visuais.CONFIG)

    with tile("por-municipio"):
        titulo(f"{medida} por município", ICONES_MEDIDA[medida])
        por_mun = tirar_pequenos(calcular(mun, ["municipio", "uf"], medida)).head(40)
        with st.container(height=520, border=False):
            st.plotly_chart(visuais.barras(por_mun, "municipio", medida),
                            width="stretch", config=visuais.CONFIG)

with col_meio:
    with tile("mapa"):
        titulo(medida, ICONES_MEDIDA[medida])
        no_mapa = tirar_pequenos(
            calcular(mun, ["cod_municipio", "municipio", "uf", "latitude", "longitude"], medida)
        )
        fig = visuais.mapa(no_mapa, medida, tabelas["fundo"], tabelas["contornos"], ufs)
        st.plotly_chart(fig, width="stretch", config=visuais.CONFIG)

    with tile("cid"):
        titulo(f"{medida} por diagnóstico (CID-10)", ICONES_MEDIDA[medida])
        por_cid = tirar_pequenos(calcular(cid, ["cid", "descricao", "capitulo_cid"], medida)).head(60)
        tabela_cid = visuais.tabela(
            visuais.linhas_cid(por_cid),
            [("cid", "CID", "cod"), ("descricao", "Nome", "nome"), ("icone", "", "ico")],
            medida,
        )
        html(f'<div class="rolagem">{tabela_cid}</div>')

with col_dir, tile("tabela-sistema"):
    titulo(f"{medida} por sistema", ICONES_MEDIDA[medida])
    por_sistema = calcular(perfil, ["capitulo_cid"], medida)
    tabela_sistema = visuais.tabela(
        visuais.linhas_sistema(por_sistema),
        [("sistema", "Sistema", "nome"), ("icone", "", "ico")],
        medida, destaque=sistema, total=total(perfil, medida),
    )
    html(f'<div class="rolagem rolagem-alta">{tabela_sistema}</div>')


st.caption(
    "Fonte: Ministério da Saúde · SIH/SUS · DATASUS · IBGE. "
    "Faixa etária, raça/cor e sexo filtram o número do topo e a tabela por sistema. "
    "Feito por [Adryan Silva Santos](https://github.com/AdryanSilva1)."
)
