# =============================================================
# app.py — SUS Sul Analytics
#
# Como rodar:
#   pip install -r requirements.txt
#   python -m streamlit run app.py
#
# O topo é igual em todas as páginas (dashboard/topo.py) e cada página
# fica num arquivo em dashboard/paginas/.
# =============================================================

from pathlib import Path

import streamlit as st

from dashboard import topo
from dashboard.componentes import html
from dashboard.dados import carregar
from dashboard.paginas import PAGINAS

st.set_page_config(page_title="SUS Sul Analytics", page_icon="🏥", layout="wide")
html(f"<style>{(Path(__file__).parent / 'dashboard' / 'styles.css').read_text(encoding='utf-8')}</style>")

try:
    tabelas, controle = carregar()
except FileNotFoundError:
    st.info("Ainda não há dados. Rode primeiro: `python -m pipeline.run`")
    st.stop()

navegacao = st.navigation(
    [st.Page(lambda m=modulo: m.mostrar(painel), title=nome, url_path=caminho, default=i == 0)
     for i, (caminho, (nome, modulo)) in enumerate(PAGINAS.items())],
    position="top",
)
painel = topo.montar(tabelas, controle)
navegacao.run()

st.caption("Fonte: Ministério da Saúde · SIH/SUS · DATASUS · IBGE. "
           "Feito por [Adryan Silva Santos](https://github.com/AdryanSilva1).")
