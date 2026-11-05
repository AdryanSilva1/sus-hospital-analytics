"""Figuras Plotly do painel. Nenhuma função aqui lê dados ou mexe em filtro."""

import plotly.graph_objects as go

from dashboard.medidas import formatar

# Uma cor por estado, igual em todos os visuais
CORES_UF = {"PR": "#2E86AB", "SC": "#E4572E", "RS": "#F3A712"}
AZUL = "#1F4E79"
AZUL_CLARO = "#9DBBD6"
CINZA = "#D5DBE3"

# Cores das regiões, na ordem da maior para a menor (parecidas com as do Power BI)
PALETA = ["#3A9BBF", "#E2BEC3", "#EFE84A", "#F47A69", "#7D8A8E", "#E9B83C", "#A6908F",
          "#6BBF8A", "#9C7BC0", "#5DA9E9", "#F29E4C", "#B5C99A"]

CONFIG = {"displayModeBar": False}

_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, Inter, sans-serif", color="#2B2B2B", size=13),
    separators=",.",
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#C9D1DB", font_size=13),
    margin=dict(l=0, r=0, t=4, b=0),
    showlegend=False,
    clickmode="event+select",
    dragmode=False,
)

# Sem isso o Plotly apaga as barras que não foram clicadas
_SEM_APAGAR = dict(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)))

_DICA_CLIQUE = "<span style='color:#888'>clique para filtrar</span>"


def _texto(valores, medida, formatador):
    formatador = formatador or (lambda v: formatar(v, medida))
    return [formatador(v) for v in valores]


def cores_por(valores):
    """Uma cor da paleta para cada valor (ex.: região), na ordem recebida."""
    return {v: PALETA[i % len(PALETA)] for i, v in enumerate(valores)}


def _cores(dados, chave, selecionado, cor):
    """cor: uma cor fixa, "uf", ou (coluna, {valor: cor}) para colorir por outra coluna."""
    if cor == "uf":
        cores = [CORES_UF.get(u, AZUL) for u in dados["uf"]]
    elif isinstance(cor, tuple):
        coluna, mapa_cores = cor
        cores = [mapa_cores.get(v, CINZA) for v in dados[coluna]]
    else:
        cores = [cor] * len(dados)
    if selecionado is None:
        return cores
    return [c if k == selecionado else CINZA for c, k in zip(cores, dados[chave])]


def barras(dados, rotulo, medida, chave, selecionado=None, cor=AZUL, altura=None,
           ordenar=True, formatador=None, clicavel=True):
    """Barras horizontais. `chave` é a coluna enviada para o filtro no clique."""
    if ordenar:
        dados = dados.sort_values("valor", ascending=False)

    fig = go.Figure(go.Bar(
        x=dados["valor"], y=dados[rotulo], orientation="h",
        text=_texto(dados["valor"], medida, formatador),
        textposition="outside", cliponaxis=False, textfont=dict(size=12, color="#333"),
        marker=dict(color=_cores(dados, chave, selecionado, cor)),
        customdata=[[k] for k in dados[chave]],
        hovertemplate="<b>%{y}</b><br>" + medida + ": %{text}"
                      + ("<br>" + _DICA_CLIQUE if clicavel else "") + "<extra></extra>",
        **_SEM_APAGAR,
    ))
    maior = dados["valor"].max() if len(dados) else 1
    fig.update_layout(
        **_BASE,
        height=altura or max(140, 25 * len(dados) + 10),
        xaxis=dict(visible=False, range=[0, maior * 1.3], fixedrange=True),
        yaxis=dict(title="", autorange="reversed", fixedrange=True,
                   categoryorder="array", categoryarray=list(dados[rotulo])),
        bargap=0.28,
    )
    return fig


def colunas(dados, rotulo, medida, cor=AZUL, altura=200):
    """Barras verticais simples (ex.: gasto por ano)."""
    fig = go.Figure(go.Bar(
        x=dados[rotulo].astype(str), y=dados["valor"], text=_texto(dados["valor"], medida, None),
        textposition="outside", cliponaxis=False, marker_color=cor,
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        **_BASE, height=altura,
        xaxis=dict(title="", type="category", fixedrange=True),
        yaxis=dict(visible=False, range=[0, dados["valor"].max() * 1.2], fixedrange=True),
    )
    return fig


def linha_mensal(atual, anterior, medida, ano, meses):
    """Evolução mês a mês do ano escolhido, com o ano anterior pontilhado atrás."""
    fig = go.Figure()
    for dados, nome, cor, traco in [(anterior, ano - 1, AZUL_CLARO, "dot"), (atual, ano, AZUL, "solid")]:
        if dados is None or dados.empty:
            continue
        dados = dados.sort_values("mes")
        fig.add_trace(go.Scatter(
            x=[meses[m - 1] for m in dados["mes"]], y=dados["valor"], name=str(nome),
            mode="lines+markers", line=dict(color=cor, width=3, dash=traco), marker=dict(size=7),
            text=_texto(dados["valor"], medida, None),
            hovertemplate=f"<b>%{{x}}/{nome}</b><br>{medida}: %{{text}}<extra></extra>",
        ))

    fig.update_layout(
        **{**_BASE, "showlegend": True}, height=260, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(title="", categoryorder="array", categoryarray=meses, fixedrange=True),
        yaxis=dict(title="", gridcolor="#EEF1F5", fixedrange=True, rangemode="tozero",
                   tickformat=",.0f"),
    )
    return fig


# ── Mapa ─────────────────────────────────────────────────────

# Enquadramento de cada recorte: (lon mín, lon máx, lat mín, lat máx)
VISTAS = {
    "Sul": (-58.0, -47.8, -34.0, -22.4),
    "PR": (-54.8, -47.9, -26.8, -22.4),
    "SC": (-54.0, -48.2, -29.5, -25.8),
    "RS": (-57.8, -49.5, -33.9, -26.9),
}

# Zoom inicial do mapa de ruas para caber o recorte inteiro
ZOOM_RUAS = {"Sul": 4.7, "PR": 5.6, "SC": 6.0, "RS": 5.4}


def _bolhas(dados, medida, malha, selecionado, formatador, cores):
    """Traços de bolhas, um por cor (estado ou região), servindo aos dois tipos de mapa."""
    coluna_cor, mapa_cores = cores or ("uf", CORES_UF)
    dados = dados.merge(malha["centros"], on="cod_municipio")
    dados = dados[dados["valor"] > 0].sort_values("valor", ascending=False)
    maior = dados["valor"].max() if len(dados) else 1

    camadas = []
    for grupo_cor, grupo in dados.groupby(coluna_cor):
        escolhido = grupo["cod_municipio"] == selecionado
        camadas.append(dict(
            cor=mapa_cores.get(grupo_cor, AZUL), nome=grupo_cor, lon=grupo["lon"], lat=grupo["lat"],
            tamanho=5 + 26 * (grupo["valor"] / maior) ** 0.5,
            opacidade=[0.9 if e or selecionado is None else 0.25 for e in escolhido],
            escolhido=escolhido,
            customdata=[
                [c, n, v, formatar(i, "Internações"), formatar(o, "Óbitos"), formatar(r, "Valor AIH")]
                for c, n, v, i, o, r in zip(
                    grupo["cod_municipio"], grupo["municipio"],
                    _texto(grupo["valor"], medida, formatador),
                    grupo["internacoes"], grupo["obitos"], grupo["valor_total"])
            ],
            hover=(
                "<b>%{customdata[1]}</b> (" + str(grupo_cor) + ")<br>"
                "<b>" + medida + ": %{customdata[2]}</b><br>"
                "Internações: %{customdata[3]}<br>"
                "Óbitos: %{customdata[4]}<br>"
                "Valor pago: %{customdata[5]}<br>" + _DICA_CLIQUE + "<extra></extra>"
            ),
        ))
    return camadas


# Do azul bem claro ao azul escuro do painel
ESCALA = [[0, "#E3EEF8"], [0.35, "#8DBFE3"], [0.7, "#3A86C4"], [1, "#123A63"]]


def mapa_pintado(dados, medida, malha, vista, selecionado=None, formatador=None, altura=600):
    """Cada município pintado do claro ao escuro pela medida, com as divisas do IBGE.

    Zoom com a rodinha, arrastar e clicar num município para filtrar.
    """
    ufs = ["PR", "SC", "RS"] if vista == "Sul" else [vista]
    geo = {"type": "FeatureCollection",
           "features": [m for m in malha["geojson"]["features"] if m["properties"]["uf"] in ufs]}
    todos = [m["id"] for m in geo["features"]]
    contorno = dict(line=dict(color="#FFFFFF", width=0.4))

    fig = go.Figure()
    # Fundo: os municípios sem dado ficam cinza
    fig.add_trace(go.Choropleth(
        geojson=geo, locations=todos, z=[0] * len(todos), showscale=False,
        colorscale=[[0, "#E9EDF2"], [1, "#E9EDF2"]], marker=contorno, hoverinfo="skip",
    ))

    dados = dados[dados["valor"] > 0]
    fig.add_trace(go.Choropleth(
        geojson=geo, locations=dados["cod_municipio"], z=dados["valor"],
        colorscale=ESCALA, marker=contorno,
        customdata=[[c, n, t] for c, n, t in zip(dados["cod_municipio"], dados["municipio"],
                                                 _texto(dados["valor"], medida, formatador))],
        hovertemplate="<b>%{customdata[1]}</b><br>" + medida + ": %{customdata[2]}<br>"
                      + _DICA_CLIQUE + "<extra></extra>",
        colorbar=dict(thickness=10, len=0.55, outlinewidth=0, title="", tickformat=",.0f"),
        **_SEM_APAGAR,
    ))

    if selecionado in set(todos):
        fig.add_trace(go.Choropleth(
            geojson=geo, locations=[selecionado], z=[0], showscale=False,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker=dict(line=dict(color="#E4572E", width=3)), hoverinfo="skip",
        ))

    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator",
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**{**_BASE, "dragmode": "pan"}, height=altura)
    return fig


def mapa(dados, medida, malha, vista, selecionado=None, com_ruas=False, formatador=None,
         cores=None, altura=600):
    """Bolhas por município. `dados` precisa de cod_municipio, municipio, uf e das métricas.

    com_ruas=False: divisa dos municípios do IBGE desenhada em SVG (abre em qualquer navegador).
    com_ruas=True: mapa de ruas (OpenStreetMap/CARTO) por baixo; precisa de internet e WebGL.
    cores: (coluna, {valor: cor}) para colorir as bolhas; sem isso, a cor é o estado.
    """
    ufs = ["PR", "SC", "RS"] if vista == "Sul" else [vista]
    camadas = _bolhas(dados, medida, malha, selecionado, formatador, cores)
    lon_min, lon_max, lat_min, lat_max = VISTAS[vista]
    fig = go.Figure()

    if com_ruas:
        for c in camadas:
            fig.add_trace(go.Scattermap(
                lon=c["lon"], lat=c["lat"], mode="markers",
                marker=dict(size=c["tamanho"], color=c["cor"], opacity=c["opacidade"]),
                customdata=c["customdata"], hovertemplate=c["hover"], **_SEM_APAGAR,
            ))
        centro = dict(lon=(lon_min + lon_max) / 2, lat=(lat_min + lat_max) / 2)
        fig.update_layout(
            **{**_BASE, "dragmode": "pan"}, height=altura,
            map=dict(style="carto-positron", center=centro, zoom=ZOOM_RUAS[vista]),
        )
        return fig

    for uf in ufs:
        xs, ys = malha["contornos"].get(uf, ([], []))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", line=dict(color="#C9D2DD", width=0.5), hoverinfo="skip",
        ))

    for c in camadas:
        fig.add_trace(go.Scatter(
            x=c["lon"], y=c["lat"], mode="markers",
            marker=dict(
                size=c["tamanho"], color=c["cor"], opacity=c["opacidade"],
                line=dict(color=["#111" if e else "#FFF" for e in c["escolhido"]],
                          width=[2.5 if e else 0.8 for e in c["escolhido"]]),
            ),
            customdata=c["customdata"], hovertemplate=c["hover"], **_SEM_APAGAR,
        ))

    fig.update_layout(
        **{**_BASE, "dragmode": "pan"}, height=altura,
        xaxis=dict(visible=False, range=[lon_min, lon_max]),
        # 1 grau de longitude vale menos que 1 de latitude nessa região (~cos 27°)
        yaxis=dict(visible=False, range=[lat_min, lat_max], scaleanchor="x", scaleratio=1 / 0.89),
    )
    return fig
