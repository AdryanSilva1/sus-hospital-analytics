"""Figuras Plotly do painel. Nenhuma função aqui lê dados ou mexe em filtro."""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dashboard.brasil import CORES_ESTADO, ESTADOS
from dashboard.medidas import MEDIDAS, formatar

# Cada estado tem a cor da sua região do Brasil, igual em todos os visuais
CORES_UF = CORES_ESTADO
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
        xaxis=dict(visible=False, range=[0, maior * 1.4], fixedrange=True),
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
    # Valores em reais vão para o eixo em milhões ("R$ 400 mi" em vez de 400.000.000)
    em_milhoes = MEDIDAS[medida][2] == "reais"
    fig = go.Figure()
    for dados, nome, cor, traco in [(anterior, ano - 1, AZUL_CLARO, "dot"), (atual, ano, AZUL, "solid")]:
        if dados is None or dados.empty:
            continue
        dados = dados.sort_values("mes")
        fig.add_trace(go.Scatter(
            x=[meses[m - 1] for m in dados["mes"]], name=str(nome),
            y=dados["valor"] / 1e6 if em_milhoes else dados["valor"],
            mode="lines+markers", line=dict(color=cor, width=3, dash=traco), marker=dict(size=7),
            text=_texto(dados["valor"], medida, None),
            hovertemplate=f"<b>%{{x}}/{nome}</b><br>{medida}: %{{text}}<extra></extra>",
        ))

    fig.update_layout(
        **{**_BASE, "showlegend": True}, height=260, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(title="", categoryorder="array", categoryarray=meses, fixedrange=True),
        yaxis=dict(title="", gridcolor="#EEF1F5", fixedrange=True, rangemode="tozero",
                   tickformat=",.0f", tickprefix="R$ " if em_milhoes else "",
                   ticksuffix=" mi" if em_milhoes else ""),
    )
    return fig


# ── Mapa ─────────────────────────────────────────────────────

def _enquadramento(malha, ufs):
    """(lon mín, lon máx, lat mín, lat máx) que cabe os estados escolhidos, com folga."""
    contornos = [malha["contornos"][uf] for uf in ufs if uf in malha["contornos"]]
    if not contornos:
        return -74.0, -34.0, -34.0, 5.5  # Brasil inteiro
    xs = np.concatenate([x for x, _ in contornos])
    ys = np.concatenate([y for _, y in contornos])
    x_min, x_max, y_min, y_max = np.nanmin(xs), np.nanmax(xs), np.nanmin(ys), np.nanmax(ys)
    folga_x, folga_y = (x_max - x_min) * 0.04, (y_max - y_min) * 0.04
    return x_min - folga_x, x_max + folga_x, y_min - folga_y, y_max + folga_y


def _zoom_para(lon_min, lon_max, lat_min, lat_max):
    """Zoom do mapa de ruas para caber a área (aproximação do zoom do MapLibre)."""
    maior_lado = max(lon_max - lon_min, (lat_max - lat_min) * 1.3)
    return max(2.5, min(9.0, math.log2(360 / maior_lado) - 0.6))


def _bolhas(dados, medida, malha, selecionado, formatador, cores):
    """Traços de bolhas, um por cor (estado ou região), servindo aos dois tipos de mapa."""
    coluna_cor, mapa_cores = cores or ("uf", CORES_UF)
    dados = dados.merge(malha["centros"], on="cod_municipio")
    dados = dados[dados["valor"] > 0].sort_values("valor", ascending=False)
    # Com muitos estados, as bolhas pequenas viram pontinhos que só pesam no navegador
    if len(dados) > MAXIMO_DE_BOLHAS:
        dados = pd.concat([dados.head(MAXIMO_DE_BOLHAS), dados[dados["cod_municipio"] == selecionado]])
    maior = dados["valor"].max() if len(dados) else 1
    menor_bolha = 3 if len(dados) > 1500 else 5  # com o Brasil inteiro, bolhas menores

    camadas = []
    for grupo_cor, grupo in dados.groupby(coluna_cor):
        escolhido = grupo["cod_municipio"] == selecionado
        camadas.append(dict(
            cor=mapa_cores.get(grupo_cor, AZUL), nome=grupo_cor, lon=grupo["lon"], lat=grupo["lat"],
            tamanho=menor_bolha + 26 * (grupo["valor"] / maior) ** 0.5,
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


MAXIMO_DE_BOLHAS = 1200

# Acima disso o mapa pintado mostra estados, não municípios (o navegador trava com o Brasil todo)
MAXIMO_DE_MUNICIPIOS = 2000

# Do azul bem claro ao azul escuro do painel
ESCALA = [[0, "#E3EEF8"], [0.35, "#8DBFE3"], [0.7, "#3A86C4"], [1, "#123A63"]]


def mapa_pintado(dados, medida, malha, ufs, selecionado=None, formatador=None, altura=600):
    """Cada município pintado do claro ao escuro pela medida, com as divisas do IBGE.

    Zoom com a rodinha, arrastar e clicar num município para filtrar.
    `dados` precisa de cod_municipio, municipio e valor.
    """
    municipios = [m for m in malha["geojson"]["features"] if m["properties"]["uf"] in ufs]
    dados = dados[dados["valor"] > 0]
    com_dado = set(dados["cod_municipio"])
    sem_dado = [m for m in municipios if m["id"] not in com_dado]

    fig = go.Figure()
    # Fundo cinza só para os municípios sem dado: o GeoJSON vai para o navegador
    # uma vez por traço, e mandar o Brasil duas vezes deixava o mapa travado
    if sem_dado:
        fig.add_trace(_pintura(sem_dado, [m["id"] for m in sem_dado]))
    fig.add_trace(_pintura(
        [m for m in municipios if m["id"] in com_dado], dados["cod_municipio"], dados["valor"],
        customdata=[[c, n, t] for c, n, t in zip(dados["cod_municipio"], dados["municipio"],
                                                 _texto(dados["valor"], medida, formatador))],
        hover="<b>%{customdata[1]}</b><br>" + medida + ": %{customdata[2]}",
    ))
    if selecionado in com_dado:
        fig.add_trace(_destaque([m for m in municipios if m["id"] == selecionado]))
    return _enquadrar_pintado(fig, altura)


def mapa_pintado_por_estado(dados, medida, malha, ufs, formatador=None, altura=600):
    """Igual ao mapa_pintado, mas um polígono por estado. `dados` precisa de uf e valor."""
    estados = [e for e in malha["estados"]["features"] if e["id"] in ufs]
    dados = dados[dados["valor"] > 0]
    fig = go.Figure(_pintura(
        estados, dados["uf"], dados["valor"],
        customdata=[[u, ESTADOS[u], t] for u, t in zip(dados["uf"],
                                                      _texto(dados["valor"], medida, formatador))],
        hover="<b>%{customdata[1]}</b><br>" + medida + ": %{customdata[2]}",
    ))
    return _enquadrar_pintado(fig, altura)


def _pintura(features, locais, valores=None, customdata=None, hover=None):
    """Um traço Choropleth. Sem `valores`, pinta tudo de cinza e não responde ao mouse."""
    geo = {"type": "FeatureCollection", "features": features}
    contorno = dict(line=dict(color="#FFFFFF", width=0.4))
    if valores is None:
        return go.Choropleth(geojson=geo, locations=locais, z=[0] * len(locais), showscale=False,
                             colorscale=[[0, "#E9EDF2"], [1, "#E9EDF2"]], marker=contorno,
                             hoverinfo="skip")
    return go.Choropleth(
        geojson=geo, locations=locais, z=valores, colorscale=ESCALA, marker=contorno,
        customdata=customdata, hovertemplate=hover + "<br>" + _DICA_CLIQUE + "<extra></extra>",
        colorbar=dict(thickness=10, len=0.55, outlinewidth=0, title="", tickformat=",.0f"),
        **_SEM_APAGAR,
    )


def _destaque(features):
    """Borda laranja em volta do município escolhido."""
    return go.Choropleth(
        geojson={"type": "FeatureCollection", "features": features},
        locations=[f["id"] for f in features], z=[0] * len(features), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker=dict(line=dict(color="#E4572E", width=3)), hoverinfo="skip",
    )


def _enquadrar_pintado(fig, altura):
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator",
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**{**_BASE, "dragmode": "pan"}, height=altura)
    return fig


def mapa(dados, medida, malha, ufs, selecionado=None, com_ruas=False, formatador=None,
         cores=None, altura=600):
    """Bolhas por município. `dados` precisa de cod_municipio, municipio, uf e das métricas.

    com_ruas=False: divisa dos municípios do IBGE desenhada em SVG (abre em qualquer navegador).
    com_ruas=True: mapa de ruas (OpenStreetMap/CARTO) por baixo; precisa de internet e WebGL.
    cores: (coluna, {valor: cor}) para colorir as bolhas; sem isso, a cor é o estado.
    """
    camadas = _bolhas(dados, medida, malha, selecionado, formatador, cores)
    lon_min, lon_max, lat_min, lat_max = _enquadramento(malha, ufs)
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
            map=dict(style="carto-positron", center=centro,
                     zoom=_zoom_para(lon_min, lon_max, lat_min, lat_max)),
        )
        return fig

    if len(ufs) == 1:
        # Um estado só: a divisa de cada município
        xs, ys = malha["contornos"].get(ufs[0], ([], []))
    else:
        # Vários estados: só a divisa dos estados, que é bem mais leve
        xs, ys = malha["divisas"]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color="#C9D2DD", width=0.6), hoverinfo="skip",
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
        # Longe do equador, 1 grau de longitude vale menos que 1 de latitude (cos da latitude)
        yaxis=dict(visible=False, range=[lat_min, lat_max], scaleanchor="x",
                   scaleratio=1 / math.cos(math.radians((lat_min + lat_max) / 2))),
    )
    return fig
