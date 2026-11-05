"""Peças de tela reaproveitadas pelas abas: blocos, cartões, gráficos e tabelas clicáveis."""

import html as html_seguro

import streamlit as st

from dashboard import filtros
from dashboard.dados import filtros_fora
from dashboard.medidas import MEDIDAS, formatar
from dashboard.visuais import CONFIG

LOGO = """
<svg width="64" height="64" viewBox="0 0 64 64">
  <circle cx="18" cy="40" r="6" fill="#9DBBD6"/><path d="M8 58c0-7 4.5-11 10-11s10 4 10 11z" fill="#9DBBD6"/>
  <circle cx="46" cy="40" r="6" fill="#9DBBD6"/><path d="M36 58c0-7 4.5-11 10-11s10 4 10 11z" fill="#9DBBD6"/>
  <circle cx="32" cy="42" r="7" fill="#1F4E79"/><path d="M20 62c0-8 5.5-13 12-13s12 5 12 13z" fill="#1F4E79"/>
  <path d="M32 31s-13-7.5-13-16a6.8 6.8 0 0 1 13-3 6.8 6.8 0 0 1 13 3c0 8.5-13 16-13 16z" fill="#F06B5B"/>
  <rect x="29.5" y="10" width="5" height="14" rx="1" fill="#fff"/>
  <rect x="25" y="14.5" width="14" height="5" rx="1" fill="#fff"/>
</svg>
"""

NOMES_FILTRO = {
    "regiao": "região", "cod_municipio": "município", "cid": "doença (CID)", "sexo": "sexo",
    "faixa_etaria": "faixa etária", "raca": "raça/cor",
    "capitulo_cid": "sistema do corpo", "tipo_procedimento": "procedimento",
}


def html(conteudo):
    # Tira recuo e linhas vazias: no Markdown, uma linha recuada depois de uma
    # linha vazia vira bloco de código e o HTML aparece como texto na tela
    linhas = (linha.strip() for linha in conteudo.splitlines())
    st.markdown("\n".join(linha for linha in linhas if linha), unsafe_allow_html=True)


def tile(chave, altura=None):
    """Caixa branca com sombra. A key vira a classe CSS st-key-tile-*.

    Com `altura`, a caixa tem altura fixa (e rolagem se precisar), para os
    blocos da mesma faixa terminarem alinhados.
    """
    return st.container(key=f"tile-{chave}", height=altura or "content", border=False)


def titulo(texto, ajuda=None):
    html(f'<div class="tile-titulo">{texto}</div>')
    if ajuda:
        st.caption(ajuda)


def cartao(icone, rotulo, valor, detalhe=None):
    """Cartão de número, no mesmo estilo do número principal do topo."""
    linha_detalhe = f'<div class="cartao-detalhe">{detalhe}</div>' if detalhe else ""
    html(f"""
        <div class="cartao">
            <div class="cartao-icone">{icone}</div>
            <div>
                <div class="cartao-rotulo">{rotulo}</div>
                <div class="cartao-valor">{valor}</div>
                {linha_detalhe}
            </div>
        </div>""")


def aviso(painel, nome, nao_tem=(), tem=()):
    """Avisa quando um filtro escolhido não vale para este visual.

    nao_tem: filtros comuns que essa tabela não tem (ex.: o fluxo não tem sistema do corpo)
    tem: filtros de foco que o visual trata por conta própria
    """
    fora = [c for c in filtros_fora(nome, painel.filtros) if c not in tem]
    fora += [c for c in nao_tem if painel.filtros.get(c) not in (None, "Todos")]
    if fora:
        nomes = ", ".join(NOMES_FILTRO[c] for c in fora)
        st.caption(f"ℹ️ Este visual não é separado por {nomes}; mostra o total sem esse filtro.")


def grafico(fig, nome=None, coluna=None, zoom=False):
    """Mostra um gráfico Plotly. Com `coluna`, o clique vira filtro nela."""
    config = {**CONFIG, "scrollZoom": zoom}
    if coluna is None:
        st.plotly_chart(fig, config=config, width="stretch")
        return

    chave = filtros.chave(nome)
    st.plotly_chart(
        fig, key=chave, config=config, width="stretch", selection_mode="points",
        on_select=lambda: filtros.ao_clicar_grafico(chave, coluna),
    )


# Formato da barra de dados de cada tipo de medida (padrão do st.column_config)
FORMATO_COLUNA = {"numero": "localized", "decimal": "%.1f", "porcentagem": "%.2f%%",
                  "reais": "localized"}


def tabela(df, colunas, nome, coluna_filtro, medida, altura=420):
    """Tabela clicável com barra de dados na coluna `valor`.

    colunas: {coluna do df: título na tela}, sem contar a coluna `valor`
    medida: nome de uma medida de MEDIDAS, ou um título livre (número inteiro)
    """
    tipo = MEDIDAS[medida][2] if medida in MEDIDAS else "numero"
    titulo_valor = f"{medida} (R$)" if tipo == "reais" else medida

    chave = filtros.chave(nome)
    valores = list(df[coluna_filtro])
    st.dataframe(
        df[[*colunas, "valor"]].rename(columns={**colunas, "valor": titulo_valor}),
        hide_index=True, height=altura, width="stretch",
        selection_mode="single-row", key=chave,
        on_select=lambda: filtros.ao_clicar_tabela(chave, coluna_filtro, valores),
        column_config={
            # Colunas de título curto (CID, UF, ícone) ficam estreitas
            **{t: st.column_config.Column(width="small" if len(t) <= 3 else "medium")
               for t in colunas.values()},
            titulo_valor: st.column_config.ProgressColumn(
                titulo_valor, format=FORMATO_COLUNA[tipo], min_value=0, width="medium",
                max_value=float(df["valor"].max()) if len(df) else 1.0,
            ),
        },
    )


def tabela_pbi(linhas, colunas, medida, destaque=None, total=None):
    """Tabela HTML no estilo do Power BI: cabeçalho escuro e barra de dados no indicador.

    linhas: lista de dicts com as chaves de `colunas` e `valor`
    colunas: lista de (chave, título, classe css)
    """
    maior = max((linha["valor"] for linha in linhas), default=0) or 1
    cabecalho = "".join(f'<th class="{c}">{html_seguro.escape(t)}</th>' for _, t, c in colunas)

    corpo = []
    for linha in linhas:
        classe = ' class="destaque"' if destaque and destaque in linha.values() else ""
        celulas = "".join(f'<td class="{c}">{html_seguro.escape(str(linha[k]))}</td>'
                          for k, _, c in colunas)
        largura = linha["valor"] / maior * 100
        corpo.append(f'<tr{classe}>{celulas}<td class="num barra"><div style="width:{largura:.1f}%">'
                     f'</div><span>{formatar(linha["valor"], medida)}</span></td></tr>')

    rodape = ""
    if total is not None:
        rodape = (f'<tfoot><tr><td colspan="{len(colunas)}">Total</td>'
                  f'<td class="num">{formatar(total, medida)}</td></tr></tfoot>')

    return (f'<table class="tabela-pbi"><thead><tr>{cabecalho}<th class="num">Indicador</th></tr>'
            f'</thead><tbody>{"".join(corpo)}</tbody>{rodape}</table>')
