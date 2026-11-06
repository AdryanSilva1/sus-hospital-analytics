"""Gráficos de barra e de linha do painel. Nenhuma função aqui lê dados ou mexe em filtro."""

import plotly.graph_objects as go

from dashboard import tema
from dashboard.medidas import MEDIDAS


def barras(dados, rotulo, medida, chave, selecionado=None, altura=None,
           ordenar=True, formatador=None, clicavel=True, cor=None):
    """Barras horizontais. `chave` é a coluna enviada para o filtro no clique."""
    if ordenar:
        dados = dados.sort_values("valor", ascending=False)

    fig = go.Figure(go.Bar(
        x=dados["valor"], y=dados[rotulo], orientation="h",
        text=tema.texto(dados["valor"], medida, formatador),
        textposition="outside", cliponaxis=False, textfont=dict(size=12),
        marker=dict(color=tema.com_destaque(dados[chave], selecionado, tema.cores_do_grupo(dados, cor))),
        customdata=[[k] for k in dados[chave]],
        hovertemplate="<b>%{y}</b><br>" + medida + ": %{text}"
                      + ("<br>" + tema.dica_clique() if clicavel else "") + "<extra></extra>",
        **tema.SEM_APAGAR,
    ))
    maior = dados["valor"].max() if len(dados) else 1
    fig.update_layout(
        **tema.base(),
        height=altura or max(140, 25 * len(dados) + 10),
        xaxis=dict(visible=False, range=[0, maior * 1.4], fixedrange=True),
        yaxis=dict(title="", autorange="reversed", fixedrange=True,
                   categoryorder="array", categoryarray=list(dados[rotulo])),
        bargap=0.28,
    )
    return fig


def colunas(dados, rotulo, medida, destaque=None, altura=200):
    """Barras verticais simples (ex.: gasto por ano). `destaque` é o rótulo em foco."""
    cores = tema.atual()
    fig = go.Figure(go.Bar(
        x=dados[rotulo].astype(str), y=dados["valor"], text=tema.texto(dados["valor"], medida, None),
        textposition="outside", cliponaxis=False,
        marker_color=[cores["destaque"] if r == destaque else cores["barra"] for r in dados[rotulo]],
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        **tema.base(), height=altura,
        xaxis=dict(title="", type="category", fixedrange=True),
        yaxis=dict(visible=False, range=[0, dados["valor"].max() * 1.2], fixedrange=True),
    )
    return fig


def linha_mensal(atual, anterior, medida, ano, meses):
    """Evolução mês a mês do ano escolhido, com o ano anterior pontilhado atrás."""
    # Valores em reais vão para o eixo em milhões ("R$ 400 mi" em vez de 400.000.000)
    em_milhoes = MEDIDAS[medida][2] == "reais"
    cores = tema.atual()
    fig = go.Figure()
    for dados, nome, cor, traco in [(anterior, ano - 1, cores["anterior"], "dot"),
                                    (atual, ano, cores["barra"], "solid")]:
        if dados is None or dados.empty:
            continue
        dados = dados.sort_values("mes")
        fig.add_trace(go.Scatter(
            x=[meses[m - 1] for m in dados["mes"]], name=str(nome),
            y=dados["valor"] / 1e6 if em_milhoes else dados["valor"],
            mode="lines+markers", line=dict(color=cor, width=2.5, dash=traco), marker=dict(size=6),
            text=tema.texto(dados["valor"], medida, None),
            hovertemplate=f"<b>%{{x}}/{nome}</b><br>{medida}: %{{text}}<extra></extra>",
        ))

    fig.update_layout(
        **{**tema.base(), "showlegend": True}, height=260, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(title="", categoryorder="array", categoryarray=meses, fixedrange=True),
        yaxis=dict(title="", gridcolor=cores["grade"], fixedrange=True, rangemode="tozero",
                   tickformat=",.0f", tickprefix="R$ " if em_milhoes else "",
                   ticksuffix=" mi" if em_milhoes else ""),
    )
    return fig
