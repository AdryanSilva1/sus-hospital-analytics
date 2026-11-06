"""Figuras Plotly do painel. Nenhuma função aqui lê dados ou mexe em filtro."""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.brasil import ESTADOS, REGIAO_DO_ESTADO
from dashboard.medidas import MEDIDAS, formatar

# Cada região do Brasil tem uma cor, e os estados usam a cor da sua região.
# Quando algo é clicado, ele fica com a cor e o resto fica cinza (como no Power BI).
CORES_REGIAO = {
    "Norte": "#2A9D8F", "Nordeste": "#F4A261", "Centro-Oeste": "#E9C46A",
    "Sudeste": "#457B9D", "Sul": "#E76F51",
}
CORES_ESTADO = {uf: CORES_REGIAO[regiao] for uf, regiao in REGIAO_DO_ESTADO.items()}

# Para as regiões do IBGE dentro de um estado (que mudam de estado para estado)
PALETA = ["#3A9BBF", "#E76F51", "#E9C46A", "#2A9D8F", "#9C7BC0", "#F4A261", "#457B9D",
          "#6BBF8A", "#D16BA5", "#5DA9E9", "#B08968", "#8AB17D"]

MAXIMO_DE_BOLHAS = 1200

# Acima disso o mapa pintado mostra estados, não municípios (o navegador trava com o Brasil todo)
MAXIMO_DE_MUNICIPIOS = 2000

TEMAS = {
    "light": {
        "barra": "#3A86C4", "apagado": "#D9DCE1", "forte": "#1F4E79", "fraco": "#71717A",
        "destaque": "#1F4E79", "anterior": "#B4B4BC",
        "obito": "#DC2626", "bloco": "#FFFFFF", "borda": "#E4E4E7", "grade": "#F0F0F2",
        "sem_dado": "#F0F0F2", "ruas": "carto-positron",
        "escala": [[0, "#E3EEF8"], [0.35, "#8DBFE3"], [0.7, "#3A86C4"], [1, "#123A63"]],
        "regioes": {"Norte": "#DCEDE7", "Nordeste": "#F5E6D6", "Centro-Oeste": "#F2EDD3",
                    "Sudeste": "#DDE5EF", "Sul": "#F0DEDB"},
    },
    "dark": {
        "barra": "#5DA9E9", "apagado": "#3A3A40", "forte": "#93C5FD", "fraco": "#A1A1AA",
        "destaque": "#BFDBFE", "anterior": "#52525B",
        "obito": "#F87171", "bloco": "#161618", "borda": "#2E2E33", "grade": "#232327",
        "sem_dado": "#1F1F23", "ruas": "carto-darkmatter",
        "escala": [[0, "#1E2A3A"], [0.35, "#2F5D8A"], [0.7, "#5DA9E9"], [1, "#DBEAFE"]],
        "regioes": {"Norte": "#1E302B", "Nordeste": "#33291F", "Centro-Oeste": "#302D1E",
                    "Sudeste": "#1F2733", "Sul": "#332322"},
    },
}

CONFIG = {"displayModeBar": False}

# Sem isso o Plotly apaga as barras que não foram clicadas
_SEM_APAGAR = dict(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)))


def _tema():
    return TEMAS["dark" if st.context.theme.type == "dark" else "light"]


def _base():
    # A cor do texto e da grade fica com o tema do Streamlit, que acompanha o claro/escuro
    tema = _tema()
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13),
        separators=",.",
        hoverlabel=dict(bgcolor=tema["bloco"], bordercolor=tema["borda"], font_size=13,
                        font_color=tema["forte"]),
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        clickmode="event+select",
        dragmode=False,
    )


def _dica_clique():
    return f"<span style='color:{_tema()['fraco']}'>clique para filtrar</span>"


def _texto(valores, medida, formatador):
    formatador = formatador or (lambda v: formatar(v, medida))
    return [formatador(v) for v in valores]


def cores_das_regioes(nomes):
    """Uma cor da PALETA para cada região do IBGE, na ordem em que aparecem."""
    return {nome: PALETA[i % len(PALETA)] for i, nome in enumerate(dict.fromkeys(nomes))}


def _cores(chaves, selecionado, cores=None):
    """Cor de cada item: a do seu grupo (ou a padrão); com algo clicado, o resto fica cinza."""
    tema = _tema()
    cores = list(cores) if cores is not None else [tema["barra"]] * len(chaves)
    if selecionado is None:
        return cores
    return [cor if k == selecionado else tema["apagado"] for k, cor in zip(chaves, cores)]


def _cores_do_grupo(dados, cor):
    """`cor`: None (cor padrão), "uf" (cor da região do estado) ou (coluna, {valor: cor})."""
    if cor is None:
        return None
    coluna, mapa_cores = (cor, CORES_ESTADO) if cor == "uf" else cor
    return [mapa_cores.get(v, _tema()["barra"]) for v in dados[coluna]]


def barras(dados, rotulo, medida, chave, selecionado=None, altura=None,
           ordenar=True, formatador=None, clicavel=True, cor=None):
    """Barras horizontais. `chave` é a coluna enviada para o filtro no clique."""
    if ordenar:
        dados = dados.sort_values("valor", ascending=False)

    fig = go.Figure(go.Bar(
        x=dados["valor"], y=dados[rotulo], orientation="h",
        text=_texto(dados["valor"], medida, formatador),
        textposition="outside", cliponaxis=False, textfont=dict(size=12),
        marker=dict(color=_cores(dados[chave], selecionado, _cores_do_grupo(dados, cor))),
        customdata=[[k] for k in dados[chave]],
        hovertemplate="<b>%{y}</b><br>" + medida + ": %{text}"
                      + ("<br>" + _dica_clique() if clicavel else "") + "<extra></extra>",
        **_SEM_APAGAR,
    ))
    maior = dados["valor"].max() if len(dados) else 1
    fig.update_layout(
        **_base(),
        height=altura or max(140, 25 * len(dados) + 10),
        xaxis=dict(visible=False, range=[0, maior * 1.4], fixedrange=True),
        yaxis=dict(title="", autorange="reversed", fixedrange=True,
                   categoryorder="array", categoryarray=list(dados[rotulo])),
        bargap=0.28,
    )
    return fig


def colunas(dados, rotulo, medida, destaque=None, altura=200):
    """Barras verticais simples (ex.: gasto por ano). `destaque` é o rótulo em foco."""
    fig = go.Figure(go.Bar(
        x=dados[rotulo].astype(str), y=dados["valor"], text=_texto(dados["valor"], medida, None),
        textposition="outside", cliponaxis=False,
        marker_color=[_tema()["destaque"] if r == destaque else _tema()["barra"] for r in dados[rotulo]],
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        **_base(), height=altura,
        xaxis=dict(title="", type="category", fixedrange=True),
        yaxis=dict(visible=False, range=[0, dados["valor"].max() * 1.2], fixedrange=True),
    )
    return fig


def linha_mensal(atual, anterior, medida, ano, meses):
    """Evolução mês a mês do ano escolhido, com o ano anterior pontilhado atrás."""
    # Valores em reais vão para o eixo em milhões ("R$ 400 mi" em vez de 400.000.000)
    em_milhoes = MEDIDAS[medida][2] == "reais"
    tema = _tema()
    fig = go.Figure()
    for dados, nome, cor, traco in [(anterior, ano - 1, tema["anterior"], "dot"),
                                    (atual, ano, tema["barra"], "solid")]:
        if dados is None or dados.empty:
            continue
        dados = dados.sort_values("mes")
        fig.add_trace(go.Scatter(
            x=[meses[m - 1] for m in dados["mes"]], name=str(nome),
            y=dados["valor"] / 1e6 if em_milhoes else dados["valor"],
            mode="lines+markers", line=dict(color=cor, width=2.5, dash=traco), marker=dict(size=6),
            text=_texto(dados["valor"], medida, None),
            hovertemplate=f"<b>%{{x}}/{nome}</b><br>{medida}: %{{text}}<extra></extra>",
        ))

    fig.update_layout(
        **{**_base(), "showlegend": True}, height=260, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(title="", categoryorder="array", categoryarray=meses, fixedrange=True),
        yaxis=dict(title="", gridcolor=tema["grade"], fixedrange=True, rangemode="tozero",
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


def _bolhas(dados, medida, malha, ufs, selecionado, formatador, cor):
    """Posição, tamanho, cor e texto das bolhas, servindo aos dois tipos de mapa."""
    tema = _tema()
    # Com vários estados, a dica mostra o estado; com um só, a região do IBGE
    local = "uf" if len(ufs) > 1 else "regiao"
    dados = dados.merge(malha["centros"], on="cod_municipio")
    dados = dados[dados["valor"] > 0].sort_values("valor", ascending=False)
    # Com muitos estados, as bolhas pequenas viram pontinhos que só pesam no navegador
    if len(dados) > MAXIMO_DE_BOLHAS:
        dados = pd.concat([dados.head(MAXIMO_DE_BOLHAS), dados[dados["cod_municipio"] == selecionado]])
    maior = dados["valor"].max() if len(dados) else 1
    menor_bolha = 3 if len(dados) > 1500 else 5  # com o Brasil inteiro, bolhas menores

    return dict(
        lon=dados["lon"], lat=dados["lat"],
        tamanho=menor_bolha + 26 * (dados["valor"] / maior) ** 0.5,
        cor=_cores(dados["cod_municipio"], selecionado, _cores_do_grupo(dados, cor)),
        customdata=[
            [c, n, u, v, formatar(i, "Internações"), formatar(o, "Óbitos"), formatar(r, "Valor AIH")]
            for c, n, u, v, i, o, r in zip(
                dados["cod_municipio"], dados["municipio"], dados[local],
                _texto(dados["valor"], medida, formatador),
                dados["internacoes"], dados["obitos"], dados["valor_total"])
        ],
        hover=(
            "<b>%{customdata[1]}</b> (%{customdata[2]})<br>"
            "<b>" + medida + ": %{customdata[3]}</b><br>"
            "Internações: %{customdata[4]}<br>"
            f"<span style='color:{tema['obito']}'>Óbitos: %{{customdata[5]}}</span><br>"
            "Valor pago: %{customdata[6]}<br>" + _dica_clique() + "<extra></extra>"
        ),
    )


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
    tema = _tema()
    geo = {"type": "FeatureCollection", "features": features}
    contorno = dict(line=dict(color=tema["bloco"], width=0.4))
    if valores is None:
        return go.Choropleth(geojson=geo, locations=locais, z=[0] * len(locais), showscale=False,
                             colorscale=[[0, tema["sem_dado"]], [1, tema["sem_dado"]]],
                             marker=contorno, hoverinfo="skip")
    return go.Choropleth(
        geojson=geo, locations=locais, z=valores, colorscale=tema["escala"], marker=contorno,
        customdata=customdata, hovertemplate=hover + "<br>" + _dica_clique() + "<extra></extra>",
        colorbar=dict(thickness=10, len=0.55, outlinewidth=0, title="", tickformat=",.0f"),
        **_SEM_APAGAR,
    )


def _destaque(features):
    """Borda em volta do município escolhido."""
    return go.Choropleth(
        geojson={"type": "FeatureCollection", "features": features},
        locations=[f["id"] for f in features], z=[0] * len(features), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker=dict(line=dict(color=_tema()["obito"], width=3)), hoverinfo="skip",
    )


def _enquadrar_pintado(fig, altura):
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator",
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**{**_base(), "dragmode": "pan"}, height=altura)
    return fig


def mapa(dados, medida, malha, ufs, selecionado=None, com_ruas=False, formatador=None,
         altura=600, cor=None):
    """Bolhas por município. `dados` precisa de cod_municipio, municipio, uf e das métricas.

    com_ruas=False: divisa dos municípios do IBGE desenhada em SVG (abre em qualquer navegador),
    com cada estado no tom suave da sua região do Brasil.
    com_ruas=True: mapa de ruas (OpenStreetMap/CARTO) por baixo; precisa de internet e WebGL.
    cor: igual ao das barras (None, "uf" ou (coluna, {valor: cor})).
    """
    tema = _tema()
    bolhas = _bolhas(dados, medida, malha, ufs, selecionado, formatador, cor)
    marcador = dict(size=bolhas["tamanho"], color=bolhas["cor"], opacity=0.85)
    lon_min, lon_max, lat_min, lat_max = _enquadramento(malha, ufs)
    fig = go.Figure()

    if com_ruas:
        fig.add_trace(go.Scattermap(
            lon=bolhas["lon"], lat=bolhas["lat"], mode="markers", marker=marcador,
            customdata=bolhas["customdata"], hovertemplate=bolhas["hover"], **_SEM_APAGAR,
        ))
        centro = dict(lon=(lon_min + lon_max) / 2, lat=(lat_min + lat_max) / 2)
        fig.update_layout(
            **{**_base(), "dragmode": "pan"}, height=altura,
            map=dict(style=tema["ruas"], center=centro,
                     zoom=_zoom_para(lon_min, lon_max, lat_min, lat_max)),
        )
        return fig

    # Um estado só: a divisa de cada município. Vários: só a dos estados, que é bem mais leve
    contornos = malha["contornos"] if len(ufs) == 1 else malha["divisas_por_estado"]
    for uf in ufs:
        xs, ys = contornos.get(uf, ([], []))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself",
            fillcolor=tema["regioes"].get(REGIAO_DO_ESTADO.get(uf), tema["sem_dado"]),
            line=dict(color=tema["bloco"], width=0.5), hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(
        x=bolhas["lon"], y=bolhas["lat"], mode="markers",
        marker=dict(**marcador, line=dict(color=tema["bloco"], width=0.6)),
        customdata=bolhas["customdata"], hovertemplate=bolhas["hover"], **_SEM_APAGAR,
    ))

    fig.update_layout(
        **{**_base(), "dragmode": "pan"}, height=altura,
        xaxis=dict(visible=False, range=[lon_min, lon_max]),
        # Longe do equador, 1 grau de longitude vale menos que 1 de latitude (cos da latitude)
        yaxis=dict(visible=False, range=[lat_min, lat_max], scaleanchor="x",
                   scaleratio=1 / math.cos(math.radians((lat_min + lat_max) / 2))),
    )
    return fig
