# =============================================================
# app.py — SUS Sul Analytics
#
# Como rodar:
#   pip install -r requirements.txt
#   python -m streamlit run app.py
#
# Este arquivo só monta a página. Cada aba fica em dashboard/abas/.
# =============================================================

from pathlib import Path

import streamlit as st

from dashboard import filtros, topo
from dashboard.abas import doencas, fluxo, gastos, mapa, perfil, visao_geral
from dashboard.componentes import html
from dashboard.dados import carregar
from dashboard.painel import Painel

ABAS = {
    "📊 Visão geral": visao_geral,
    "💰 Gastos": gastos,
    "🗺️ Mapa e municípios": mapa,
    "🔁 Fluxo de pacientes": fluxo,
    "🩺 Doenças (CID-10)": doencas,
    "👥 Perfil do paciente": perfil,
}

st.set_page_config(page_title="SUS Sul Analytics", page_icon="🏥", layout="wide")
html(f"<style>{(Path(__file__).parent / 'dashboard' / 'styles.css').read_text(encoding='utf-8')}</style>")

try:
    tabelas, controle = carregar()
except FileNotFoundError:
    st.info("Ainda não há dados. Rode primeiro: `python -m pipeline.run`")
    st.stop()

filtros.iniciar()

ano, ultimo_mes, anos = topo.cabecalho(controle)
medida = topo.barra_de_filtros(sorted(tabelas["municipio"]["capitulo_cid"].unique()))
topo.filtros_ativos(dict(zip(tabelas["municipio"]["cod_municipio"], tabelas["municipio"]["municipio"])))

painel = Painel(tabelas, filtros.atuais(ano), medida, ano, ultimo_mes, anos)
topo.cartoes(painel)

# key + on_change mantêm a aba aberta depois de um clique que filtra.
# Só a aba aberta é calculada, o que deixa cada clique bem mais rápido.
abas = st.tabs(list(ABAS), key="aba", on_change="rerun")
aberta = st.session_state.get("aba") or next(iter(ABAS))
for aba, (nome, modulo) in zip(abas, ABAS.items()):
    if nome == aberta:
        with aba:
            modulo.mostrar(painel)

st.caption("Fonte: Ministério da Saúde · SIH/SUS · DATASUS · IBGE. "
           "Feito por [Adryan Silva Santos](https://github.com/AdryanSilva1).")
