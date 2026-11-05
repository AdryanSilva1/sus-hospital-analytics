"""Abre uma página só, com o mesmo topo do app. Usado pelo test_painel.py.

A página vem de st.session_state["pagina"] (o caminho da URL, ex.: "gastos").
"""

import streamlit as st

from dashboard import topo
from dashboard.dados import carregar
from dashboard.paginas import PAGINAS

tabelas, controle = carregar()
painel = topo.montar(tabelas, controle)
_, modulo = PAGINAS[st.session_state.get("pagina", "painel")]
modulo.mostrar(painel)
