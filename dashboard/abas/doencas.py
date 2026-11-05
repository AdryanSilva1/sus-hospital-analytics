import streamlit as st

from dashboard.componentes import aviso, html, tabela, tile, titulo
from dashboard.medidas import calcular, formatar, tirar_pequenos, total
from dashboard.topo import CARTOES


def detalhe(painel):
    cid = st.session_state.cid
    if not cid:
        titulo("Detalhe da doença")
        st.markdown("Clique numa linha da tabela para ver os números da doença.")
        return

    linhas = painel.dados("cid")
    if linhas.empty:
        titulo(cid)
        st.markdown("Sem internações com esses filtros.")
        return

    titulo(f"{cid} · {linhas['descricao'].iloc[0]}")
    for nome in CARTOES:
        html(f'<div class="linha-detalhe"><span>{nome}</span>'
             f'<b>{formatar(total(linhas, nome), nome)}</b></div>')

    sistema = linhas["capitulo_cid"].iloc[0]
    do_sistema = painel.dados("cid", ignorar=["cid"], capitulo_cid=sistema)
    parte = linhas["internacoes"].sum() / max(do_sistema["internacoes"].sum(), 1) * 100
    st.caption(f"Representa {parte:.1f}% das internações do sistema {sistema}.".replace(".", ",", 1))


def mostrar(painel):
    esq, dir_ = st.columns([1.6, 1])

    with esq, tile("cid-tabela"):
        titulo(f"{painel.medida} por doença (CID-10)")
        df = calcular(painel.dados("cid", ignorar=["cid"]), ["cid", "descricao", "capitulo_cid"],
                      painel.medida)
        tabela(tirar_pequenos(df, painel.medida),
               {"cid": "CID", "descricao": "Doença", "capitulo_cid": "Sistema"},
               "cid-tabela", "cid", painel.medida, altura=600)
        aviso(painel, "cid")

    with dir_, tile("cid-detalhe"):
        detalhe(painel)
