import html

import plotly.express as px
import plotly.graph_objects as go

from dashboard.dados import ICONES_SISTEMA, formatar

# Uma cor por estado, igual em todos os visuais
CORES_UF = {"PR": "#3A9BBF", "SC": "#F06B5B", "RS": "#F2C14E"}

CONFIG = {"displayModeBar": False}

_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, Inter, sans-serif", color="#3B3B3B", size=13),
    separators=",.",
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D0D7E2", font_size=13),
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
)


def barras(dados, rotulo, medida, altura=None):
    """Barras horizontais com o valor na ponta, coloridas pelo estado."""
    dados = dados.copy()
    dados["texto"] = dados["valor"].map(lambda v: formatar(v, medida))

    fig = px.bar(
        dados, x="valor", y=rotulo, orientation="h", text="texto",
        color="uf", color_discrete_map=CORES_UF,
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False, width=0.72,
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    )
    fig.update_layout(
        **_BASE,
        height=altura or max(160, 30 * len(dados)),
        xaxis=dict(visible=False, range=[0, dados["valor"].max() * 1.28]),
        yaxis=dict(title="", autorange="reversed", categoryorder="array",
                   categoryarray=list(dados[rotulo]), tickfont=dict(size=13)),
        bargap=0.25,
    )
    return fig


def mapa(dados, medida, fundo=None, contornos=None, ufs=("PR", "SC", "RS")):
    """Mapa em bolhas desenhado com eixos de latitude/longitude.

    Não depende de serviço de mapas externo: o fundo são os contornos dos
    estados (IBGE) e um pontinho cinza para cada município.
    """
    fig = go.Figure()

    if contornos is not None:
        for _, trecho in contornos[contornos["uf"].isin(ufs)].groupby("trecho"):
            fig.add_trace(go.Scatter(
                x=trecho["lon"], y=trecho["lat"], mode="lines", fill="toself",
                fillcolor="#F4F6F9", line=dict(color="#B8C2CE", width=1), hoverinfo="skip",
            ))

    if fundo is not None:
        pontos = fundo[fundo["uf"].isin(ufs)]
        fig.add_trace(go.Scatter(
            x=pontos["longitude"], y=pontos["latitude"], mode="markers",
            marker=dict(size=3, color="#C9D1DB"), hoverinfo="skip",
        ))

    dados = dados.dropna(subset=["latitude", "longitude"])
    dados = dados[dados["valor"] > 0].sort_values("valor", ascending=False)
    tamanho = 5 + 26 * (dados["valor"] / dados["valor"].max()) ** 0.5 if len(dados) else []

    for uf, grupo in dados.groupby("uf"):
        fig.add_trace(go.Scatter(
            x=grupo["longitude"], y=grupo["latitude"], mode="markers",
            marker=dict(size=tamanho[grupo.index], color=CORES_UF[uf], opacity=0.8,
                        line=dict(color="#FFFFFF", width=0.8)),
            text=grupo["municipio"],
            customdata=[formatar(v, medida) for v in grupo["valor"]],
            hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
        ))

    fig.update_layout(
        **_BASE, height=470,
        xaxis=dict(visible=False),
        # 1 grau de longitude vale menos que 1 de latitude nessa região (~cos 27°)
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1 / 0.89),
    )
    return fig


def tabela(linhas, colunas, medida, destaque=None, total=None):
    """Tabela HTML no estilo do Power BI: cabeçalho escuro e barra de dados na última coluna.

    linhas: lista de dicts com as chaves de 'colunas' + 'valor'
    colunas: lista de (chave, título, classe css)
    """
    maior = max((l["valor"] for l in linhas), default=0) or 1

    cabecalho = "".join(f'<th class="{c}">{html.escape(t)}</th>' for _, t, c in colunas)
    cabecalho += '<th class="num">Indicador</th>'

    corpo = []
    for l in linhas:
        classe = ' class="destaque"' if destaque and l.get("sistema") == destaque else ""
        celulas = "".join(f'<td class="{c}">{html.escape(str(l[k]))}</td>' for k, _, c in colunas)
        largura = l["valor"] / maior * 100
        barra = (
            f'<td class="num barra"><div style="width:{largura:.1f}%"></div>'
            f'<span>{formatar(l["valor"], medida)}</span></td>'
        )
        corpo.append(f"<tr{classe}>{celulas}{barra}</tr>")

    rodape = ""
    if total is not None:
        vazias = "".join("<td></td>" for _ in colunas[1:])
        rodape = f'<tfoot><tr><td>Total</td>{vazias}<td class="num">{formatar(total, medida)}</td></tr></tfoot>'

    return (
        f'<table class="tabela-pbi"><thead><tr>{cabecalho}</tr></thead>'
        f'<tbody>{"".join(corpo)}</tbody>{rodape}</table>'
    )


def linhas_sistema(dados):
    return [
        {"sistema": s, "icone": ICONES_SISTEMA.get(s, ""), "valor": v}
        for s, v in zip(dados["capitulo_cid"], dados["valor"])
    ]


def linhas_cid(dados):
    return [
        {"cid": c, "descricao": d, "icone": ICONES_SISTEMA.get(s, ""), "valor": v}
        for c, d, s, v in zip(dados["cid"], dados["descricao"], dados["capitulo_cid"], dados["valor"])
    ]
