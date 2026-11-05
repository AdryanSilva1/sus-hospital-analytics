import streamlit as st

LOGO = """
<svg width="54" height="54" viewBox="0 0 64 64">
  <rect x="2" y="2" width="60" height="60" rx="14" fill="#E9F3FB"/>
  <path d="M32 50s-17-10.5-17-22a9 9 0 0 1 17-4.2A9 9 0 0 1 49 28c0 11.5-17 22-17 22z" fill="#F06B5B"/>
  <rect x="28.5" y="21" width="7" height="20" rx="1.5" fill="#fff"/>
  <rect x="22" y="27.5" width="20" height="7" rx="1.5" fill="#fff"/>
</svg>
"""


def tile(chave):
    """Caixa branca com sombra. A key vira a classe CSS st-key-tile-*."""
    return st.container(key=f"tile-{chave}")


def titulo(texto, icone=""):
    st.markdown(f'<div class="tile-titulo">{icone} {texto}</div>', unsafe_allow_html=True)


def html(conteudo):
    st.markdown(conteudo, unsafe_allow_html=True)
