"""Parte de cima, igual em todas as páginas: cabeçalho, sistemas do corpo e filtros ativos."""

from datetime import date

import streamlit as st

from dashboard import filtros, icones
from dashboard.brasil import (
    CORES_REGIAO,
    ESTADOS,
    LOCAIS,
    REGIAO_DO_ESTADO,
    REGIOES,
    e_um_estado,
    nome_do_local,
)
from dashboard.componentes import LOGO, NOMES_FILTRO, html, tile
from dashboard.medidas import MINIMO_PARA_RAZAO, formatar, total, variacao
from dashboard.painel import MESES, Painel

AJUDA = f"""
**Como usar**
- Clique numa barra, bolha do mapa ou linha de tabela para filtrar o painel inteiro.
- Clique de novo no mesmo item, ou no ✕ do filtro, para desmarcar.
- Os botões dos sistemas do corpo filtram tudo pelo tipo de doença.

**Regras**
- Internação = AIH principal aprovada (não conta AIH de continuação).
- Município = onde fica o hospital, exceto na página Fluxo, que também mostra onde o paciente mora.
- Região = região geográfica intermediária do IBGE (no Brasil ou numa região do país, o painel
  agrupa por estado).
- Valores em R$, sem correção pela inflação. É o valor pago pelo SUS pela internação (AIH),
  não o gasto total com saúde.
- A comparação com o ano anterior usa os mesmos meses nos dois anos, e só os meses que todos
  os estados já publicaram (o DATASUS libera alguns estados antes de outros).
- Em médias e porcentagens, itens com menos de {MINIMO_PARA_RAZAO} internações ficam fora dos rankings.
- Município, doença e perfil do paciente vêm de tabelas separadas, por isso só dá para
  filtrar por um desses de cada vez.

**Não está aqui**: fila de espera, mortes na fila e reinternações (as bases públicas não
identificam o paciente).

**Fontes**: SIH/SUS e CID-10 (DATASUS); municípios, regiões, mapas e população do Censo 2022 (IBGE).
"""


def _contar_clique():
    st.session_state.versao += 1


def _rotulo_do_local(local):
    if e_um_estado(local):
        return f"{local} · {ESTADOS[local]}"
    return local if local == "Brasil" else f"Região {local}"


def _selo_do_local(local):
    """Bandeira (ou selo colorido) e a sigla grande, como no Power BI."""
    regiao = local if local in REGIOES else REGIAO_DO_ESTADO.get(local)
    cor = CORES_REGIAO.get(regiao, "#1F4E79")
    sigla = local if e_um_estado(local) else ("BR" if local == "Brasil" else local)
    classe = "sigla" if len(sigla) <= 2 else "sigla longa"
    return (f'<div class="estado">{icones.selo(local, cor)}'
            f'<span class="{classe}">{sigla}</span></div>')


def cabecalho(controle):
    """Primeira linha de blocos. Devolve (ano, último mês com dado, anos disponíveis)
    e o espaço reservado para o número principal, preenchido depois por numero_principal()."""
    anos = [int(a) for a in sorted(controle["ano"].unique(), reverse=True)]
    c_logo, c_titulo, c_uf, c_numero, c_ano, c_ajuda, c_atual = st.columns(
        [0.55, 2.2, 1.75, 1.8, 0.8, 0.5, 1.4], vertical_alignment="center")

    with c_logo, tile("logo"):
        html(f'<div class="logo">{LOGO}</div>')

    with c_uf, tile("uf"):
        bandeira, escolha = st.columns([1, 1.3], vertical_alignment="center")
        with bandeira:
            html(_selo_do_local(st.session_state.f_uf))
        with escolha:
            st.selectbox("Local", LOCAIS, key="f_uf", on_change=_contar_clique,
                         format_func=_rotulo_do_local, label_visibility="collapsed")

    with c_ano, tile("ano"):
        ano = int(st.selectbox("📅 Ano", anos, key="ano"))

    # Último mês que todos os estados já publicaram (alguns podem estar um mês à frente)
    meses_do_ano = controle.loc[controle["ano"] == ano, "ultimo_mes"]
    ultimo_mes, mes_mais_recente = int(meses_do_ano.min()), int(meses_do_ano.max())
    periodo = str(ano) if mes_mais_recente == 12 else f"{ano} · jan a {MESES[mes_mais_recente - 1]}"

    with c_titulo, tile("titulo"):
        html(f"""
            <div class="titulo-painel">Informações Hospitalares (SUS/SIH)</div>
            <div class="subtitulo-painel">{nome_do_local(st.session_state.f_uf)} · {periodo}</div>""")

    with c_ajuda, tile("ajuda"), st.popover("?"):
        st.markdown(AJUDA)

    atualizado = date.fromisoformat(controle["atualizado_em"].max())
    # Os números do ano somam o que cada estado já publicou; a comparação usa só os meses comuns
    atrasados = f" (parte até {ultimo_mes:02d})" if mes_mais_recente > ultimo_mes else ""
    with c_atual, tile("atualizado"):
        html(f"""
            <div class="atualizado">
                <div class="atualizado-icone">🗓️</div>
                <div>
                    <div class="atualizado-rotulo">Atualizado em</div>
                    <div class="atualizado-data">{atualizado:%d/%m/%Y}</div>
                    <div class="atualizado-rotulo">dados até {mes_mais_recente:02d}/{ano}{atrasados}</div>
                </div>
            </div>""")

    return ano, ultimo_mes, anos, c_numero


def numero_principal(espaco, painel):
    medida = painel.medida
    detalhe = ""
    comparacao = painel.mesmo_periodo_do_ano_anterior()
    if comparacao:
        mudanca = variacao(total(comparacao[0], medida), total(comparacao[1], medida))
        if mudanca:
            detalhe = f'<div class="kpi-detalhe">{mudanca} vs {painel.ano - 1}</div>'

    with espaco, tile("kpi"):
        html(f"""
            <div class="kpi">
                <div class="kpi-icone">{icones.MEDIDAS[medida]}</div>
                <div>
                    <div class="kpi-rotulo">{medida}</div>
                    <div class="kpi-valor">{formatar(total(painel.dados(), medida), medida)}</div>
                    {detalhe}
                </div>
            </div>""")


def _escolher_sistema(sistema):
    filtros.definir("capitulo_cid", sistema)


def sistemas():
    """Linha de botões com os sistemas do corpo (filtram tudo)."""
    escolhido = st.session_state.f_sistema
    with st.container(horizontal=True, key="sistemas", gap="small"):
        for nome in icones.BOTOES:
            st.button(nome, icon=icones.sistema(nome), key=f"sistema-{nome}",
                      type="primary" if nome == escolhido else "secondary",
                      on_click=_escolher_sistema, args=(nome,), width="stretch")


def filtros_ativos(nomes_municipio):
    """Etiquetas dos filtros em uso, cada uma com ✕ para tirar."""
    s = st.session_state
    ativos = []
    if s.f_uf != "Brasil":
        ativos.append(("f_uf", f"Local: {_rotulo_do_local(s.f_uf)}"))
    if s.f_proc != "Todos":
        ativos.append(("f_proc", f"Procedimento: {s.f_proc}"))
    if s.f_sistema != "Todos":
        ativos.append(("f_sistema", f"Sistema: {s.f_sistema}"))
    if s.regiao:
        ativos.append(("regiao", f"Região: {s.regiao}"))
    if s.cod_municipio:
        ativos.append(("cod_municipio", f"Município: {nomes_municipio.get(s.cod_municipio, '')}"))
    if s.cid:
        ativos.append(("cid", f"CID: {s.cid}"))
    for coluna in filtros.SO_PERFIL:
        if s[coluna] != "Todos":
            ativos.append((coluna, f"{NOMES_FILTRO[coluna].capitalize()}: {s[coluna]}"))

    # O container existe sempre, para a posição dos elementos de baixo não mudar
    with st.container(horizontal=True, key="chips"):
        if not ativos:
            st.caption("Clique em qualquer barra, bolha do mapa ou linha de tabela para filtrar.")
            return
        for coluna, texto in ativos:
            st.button(f"✕  {texto}", key=f"chip-{coluna}", on_click=filtros.limpar, args=([coluna],))
        st.button("Limpar tudo", key="chip-tudo", type="tertiary", on_click=filtros.limpar)


def montar(tabelas, controle):
    """Desenha o topo inteiro e devolve o Painel que as páginas recebem."""
    filtros.iniciar()
    st.session_state.setdefault("medida", "Internações")

    ano, ultimo_mes, anos, espaco_do_numero = cabecalho(controle)
    sistemas()
    filtros_ativos(dict(zip(tabelas["municipio"]["cod_municipio"], tabelas["municipio"]["municipio"])))

    painel = Painel(tabelas, filtros.atuais(ano), st.session_state.medida, ano, ultimo_mes, anos)
    numero_principal(espaco_do_numero, painel)
    return painel
