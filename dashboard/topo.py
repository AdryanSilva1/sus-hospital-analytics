"""Parte de cima do painel: cabeçalho, barra de filtros, filtros ativos e números principais."""

from datetime import date

import streamlit as st

from dashboard import filtros
from dashboard.componentes import LOGO, NOMES_FILTRO, cartao, html, tile
from dashboard.dados import filtros_fora
from dashboard.medidas import MEDIDAS, MINIMO_PARA_RAZAO, formatar, total, variacao
from dashboard.painel import MESES, NOMES_UF

# Os números do topo, nessa ordem
CARTOES = ["Internações", "Óbitos", "Porcentagem de Óbitos", "Dias por Internação",
           "Valor AIH", "Valor Médio AIH"]

AJUDA = f"""
**Como usar**
- Clique numa barra, município do mapa ou linha de tabela para filtrar o painel inteiro.
- Clique de novo no mesmo item, ou no ✕ do filtro, para desmarcar.
- A medida escolhida no topo vale para os gráficos de todas as abas.

**Regras**
- Internação = AIH principal aprovada (não conta AIH de continuação).
- Município = onde fica o hospital, exceto na aba Fluxo, que também mostra onde o paciente mora.
- Valores em R$, sem correção pela inflação. É o valor pago pelo SUS pela internação (AIH),
  não o gasto total com saúde.
- A comparação com o ano anterior usa os mesmos meses nos dois anos.
- Em médias e porcentagens, itens com menos de {MINIMO_PARA_RAZAO} internações ficam fora dos rankings.
- Município, doença e perfil do paciente vêm de tabelas separadas, por isso só dá para
  filtrar por um desses de cada vez.

**Não está aqui**: fila de espera e mortes na fila (não há base pública nacional).

**Fontes**: SIH/SUS e CID-10 (DATASUS); municípios, mapas e população do Censo 2022 (IBGE).
"""


def cabecalho(controle):
    """Desenha o topo e devolve (ano escolhido, último mês com dado nesse ano)."""
    anos = sorted(controle["ano"].unique(), reverse=True)
    c_titulo, c_ano, c_atual, c_ajuda = st.columns([4.2, 1, 1.6, 0.5], vertical_alignment="center")

    with c_ano, tile("ano"):
        ano = int(st.selectbox("Ano", anos, key="ano"))

    ultimo_mes = int(controle.loc[controle["ano"] == ano, "ultimo_mes"].min())
    periodo = str(ano) if ultimo_mes == 12 else f"{ano} · jan a {MESES[ultimo_mes - 1]}"
    atualizado = date.fromisoformat(controle["atualizado_em"].max())

    with c_titulo, tile("titulo"):
        html(f"""
            <div class="cabecalho">
                <div class="logo">{LOGO}</div>
                <div>
                    <div class="titulo-painel">Internações Hospitalares no SUS</div>
                    <div class="subtitulo-painel">
                        {NOMES_UF[st.session_state.f_uf]} · {periodo} · Fonte: SIH/SUS (DATASUS)
                    </div>
                </div>
            </div>""")

    with c_atual, tile("atualizado"):
        html(f"""
            <div class="atualizado-rotulo">Dados até {ultimo_mes:02d}/{ano}</div>
            <div class="atualizado-data">Atualizado em {atualizado:%d/%m/%Y}</div>""")

    with c_ajuda, tile("ajuda"), st.popover("?"):
        st.markdown(AJUDA)

    return ano, ultimo_mes, [int(a) for a in anos]


def _sem_vazio(chave, padrao):
    # Clicar no botão já ativo deixa o controle vazio; volta para o padrão
    if st.session_state[chave] is None:
        st.session_state[chave] = padrao
    st.session_state.versao += 1


def barra_de_filtros(sistemas):
    """Filtros fixos do topo. Devolve a medida escolhida para os gráficos."""
    with tile("filtros"):
        f1, f2, f3, f4 = st.columns([1.4, 1.3, 1.6, 1.6])
        with f1:
            st.segmented_control("Estado", ["Sul", "PR", "SC", "RS"], key="f_uf",
                                 on_change=_sem_vazio, args=("f_uf", "Sul"))
        with f2:
            st.segmented_control("Procedimento", ["Todos", "Clínico", "Cirúrgico"], key="f_proc",
                                 on_change=_sem_vazio, args=("f_proc", "Todos"))
        with f3:
            st.selectbox("Sistema do corpo (capítulo CID-10)", ["Todos", *sistemas], key="f_sistema")
        with f4:
            return st.selectbox("Medida dos gráficos", list(MEDIDAS), key="medida")


def filtros_ativos(nomes_municipio):
    """Etiquetas dos filtros em uso, cada uma com ✕ para tirar."""
    s = st.session_state
    ativos = []
    if s.f_uf != "Sul":
        ativos.append(("f_uf", f"Estado: {s.f_uf}"))
    if s.f_proc != "Todos":
        ativos.append(("f_proc", f"Procedimento: {s.f_proc}"))
    if s.f_sistema != "Todos":
        ativos.append(("f_sistema", f"Sistema: {s.f_sistema}"))
    if s.cod_municipio:
        nome = nomes_municipio.get(s.cod_municipio, s.cod_municipio)
        ativos.append(("cod_municipio", f"Município: {nome}"))
    if s.cid:
        ativos.append(("cid", f"CID: {s.cid}"))
    for coluna in filtros.SO_PERFIL:
        if s[coluna]:
            ativos.append((coluna, f"{NOMES_FILTRO[coluna].capitalize()}: {s[coluna]}"))

    # O container existe sempre, para a posição dos elementos de baixo não mudar
    with st.container(horizontal=True, key="chips"):
        if not ativos:
            st.caption("Dica: clique em qualquer barra, município do mapa ou linha de tabela para filtrar.")
            return
        for coluna, texto in ativos:
            st.button(f"✕  {texto}", key=f"chip-{coluna}", on_click=filtros.limpar, args=([coluna],))
        st.button("Limpar tudo", key="chip-tudo", type="tertiary", on_click=filtros.limpar)


def _mesmos_meses_do_ano_anterior(painel):
    """(atual, anterior) da tabela por mês, até o mesmo mês. None se não der para comparar."""
    # A tabela por mês não tem município, CID nem perfil: com esses filtros não compara
    if filtros_fora("mes", painel.filtros) or painel.ano - 1 not in painel.anos:
        return None

    atual = painel.dados("mes")
    anterior = painel.dados("mes", ano=painel.ano - 1)
    anterior = anterior[anterior["mes"] <= painel.ultimo_mes]
    return atual, anterior


def cartoes(painel):
    base = painel.dados()
    comparacao = _mesmos_meses_do_ano_anterior(painel)

    with st.container(horizontal=True, key="cartoes"):
        for nome in CARTOES:
            detalhe = None
            if comparacao:
                atual, anterior = comparacao
                mudanca = variacao(total(atual, nome), total(anterior, nome))
                if mudanca:
                    detalhe = f"{mudanca} vs {painel.ano - 1}"
            cartao(nome, formatar(total(base, nome), nome), detalhe, ativo=nome == painel.medida)
