"""Mapas do painel: bolhas por município e municípios (ou estados) pintados pela medida."""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dashboard import tema
from dashboard.brasil import ESTADOS, REGIAO_DO_ESTADO
from dashboard.medidas import formatar

MAXIMO_DE_BOLHAS = 1200

# Acima disso o mapa pintado mostra estados, não municípios (o navegador trava com o Brasil todo)
MAXIMO_DE_MUNICIPIOS = 2000


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


def _pontos(dados, medida, malha, ufs, selecionado, formatador, cor):
    """Posição, tamanho, cor e texto das bolhas, servindo aos dois tipos de mapa."""
    cores = tema.atual()
    # Com vários estados, a dica mostra o estado; com um só, a região do IBGE
    local = "uf" if len(ufs) > 1 else "regiao"
    dados = dados.merge(malha["centros"], on="cod_municipio")
    dados = dados[dados["valor"] > 0].sort_values("valor", ascending=False)
    # Com muitos estados, as bolhas pequenas viram pontinhos que só pesam no navegador
    if len(dados) > MAXIMO_DE_BOLHAS:
        dados = pd.concat([dados.head(MAXIMO_DE_BOLHAS), dados[dados["cod_municipio"] == selecionado]])
    maior = dados["valor"].max() if len(dados) else 1

    return dict(
        lon=dados["lon"], lat=dados["lat"],
        tamanho=4 + 26 * (dados["valor"] / maior) ** 0.5,
        cor=tema.com_destaque(dados["cod_municipio"], selecionado, tema.cores_do_grupo(dados, cor)),
        # Em array do numpy o Plotly monta a figura bem mais rápido que em lista de listas
        customdata=np.array([
            [c, n, u, v, formatar(i, "Internações"), formatar(o, "Óbitos"), formatar(r, "Valor AIH")]
            for c, n, u, v, i, o, r in zip(
                dados["cod_municipio"], dados["municipio"], dados[local],
                tema.texto(dados["valor"], medida, formatador),
                dados["internacoes"], dados["obitos"], dados["valor_total"])
        ], dtype=object).reshape(-1, 7),
        hover=(
            "<b>%{customdata[1]}</b> (%{customdata[2]})<br>"
            "<b>" + medida + ": %{customdata[3]}</b><br>"
            "Internações: %{customdata[4]}<br>"
            f"<span style='color:{cores['obito']}'>Óbitos: %{{customdata[5]}}</span><br>"
            "Valor pago: %{customdata[6]}<br>" + tema.dica_clique() + "<extra></extra>"
        ),
    )


def pintado(dados, medida, malha, ufs, selecionado=None, formatador=None, altura=600):
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
        customdata=np.array([[c, n, t] for c, n, t in zip(
            dados["cod_municipio"], dados["municipio"], tema.texto(dados["valor"], medida, formatador))],
            dtype=object).reshape(-1, 3),
        hover="<b>%{customdata[1]}</b><br>" + medida + ": %{customdata[2]}",
    ))
    if selecionado in com_dado:
        fig.add_trace(_destaque([m for m in municipios if m["id"] == selecionado]))
    return _enquadrar_pintado(fig, altura)


def pintado_por_estado(dados, medida, malha, ufs, formatador=None, altura=600):
    """Igual ao pintado(), mas um polígono por estado. `dados` precisa de uf e valor."""
    estados = [e for e in malha["estados"]["features"] if e["id"] in ufs]
    dados = dados[dados["valor"] > 0]
    fig = go.Figure(_pintura(
        estados, dados["uf"], dados["valor"],
        customdata=[[u, ESTADOS[u], t] for u, t in zip(dados["uf"],
                                                      tema.texto(dados["valor"], medida, formatador))],
        hover="<b>%{customdata[1]}</b><br>" + medida + ": %{customdata[2]}",
    ))
    return _enquadrar_pintado(fig, altura)


def _pintura(features, locais, valores=None, customdata=None, hover=None):
    """Um traço Choropleth. Sem `valores`, pinta tudo de cinza e não responde ao mouse."""
    cores = tema.atual()
    geo = {"type": "FeatureCollection", "features": features}
    contorno = dict(line=dict(color=cores["bloco"], width=0.4))
    if valores is None:
        return go.Choropleth(geojson=geo, locations=locais, z=[0] * len(locais), showscale=False,
                             colorscale=[[0, cores["sem_dado"]], [1, cores["sem_dado"]]],
                             marker=contorno, hoverinfo="skip")
    return go.Choropleth(
        geojson=geo, locations=locais, z=valores, colorscale=cores["escala"], marker=contorno,
        customdata=customdata, hovertemplate=hover + "<br>" + tema.dica_clique() + "<extra></extra>",
        colorbar=dict(thickness=10, len=0.55, outlinewidth=0, title="", tickformat=",.0f"),
        **tema.SEM_APAGAR,
    )


def _destaque(features):
    """Borda em volta do município escolhido."""
    return go.Choropleth(
        geojson={"type": "FeatureCollection", "features": features},
        locations=[f["id"] for f in features], z=[0] * len(features), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker=dict(line=dict(color=tema.atual()["obito"], width=3)), hoverinfo="skip",
    )


def _enquadrar_pintado(fig, altura):
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator",
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**{**tema.base(), "dragmode": "pan"}, height=altura)
    return fig


def _por_regiao(ufs):
    regioes = {}
    for uf in ufs:
        regioes.setdefault(REGIAO_DO_ESTADO.get(uf), []).append(uf)
    return regioes


def bolhas(dados, medida, malha, ufs, selecionado=None, com_ruas=False, formatador=None,
         altura=600, cor=None):
    """Bolhas por município. `dados` precisa de cod_municipio, municipio, uf e das métricas.

    com_ruas=False: divisa dos municípios do IBGE desenhada em SVG (abre em qualquer navegador),
    com cada estado no tom suave da sua região do Brasil.
    com_ruas=True: mapa de ruas (OpenStreetMap/CARTO) por baixo; precisa de internet e WebGL.
    cor: igual ao das barras (None, "uf" ou (coluna, {valor: cor})).
    """
    cores = tema.atual()
    pontos = _pontos(dados, medida, malha, ufs, selecionado, formatador, cor)
    marcador = dict(size=pontos["tamanho"], color=pontos["cor"], opacity=0.85)
    lon_min, lon_max, lat_min, lat_max = _enquadramento(malha, ufs)
    fig = go.Figure()

    if com_ruas:
        fig.add_trace(go.Scattermap(
            lon=pontos["lon"], lat=pontos["lat"], mode="markers", marker=marcador,
            customdata=pontos["customdata"], hovertemplate=pontos["hover"], **tema.SEM_APAGAR,
        ))
        centro = dict(lon=(lon_min + lon_max) / 2, lat=(lat_min + lat_max) / 2)
        fig.update_layout(
            **{**tema.base(), "dragmode": "pan"}, height=altura,
            map=dict(style=cores["ruas"], center=centro,
                     zoom=_zoom_para(lon_min, lon_max, lat_min, lat_max)),
        )
        return fig

    # Um estado só: a divisa de cada município. Vários: só a dos estados, que é bem mais leve.
    # Um traço por região do Brasil (no máximo 5), e não um por estado: menos traços, mapa mais rápido
    contornos = malha["contornos"] if len(ufs) == 1 else malha["divisas_por_estado"]
    for regiao, estados in _por_regiao(ufs).items():
        partes = [contornos[uf] for uf in estados if uf in contornos]
        if not partes:
            continue
        fig.add_trace(go.Scatter(
            x=np.concatenate([x for x, _ in partes]), y=np.concatenate([y for _, y in partes]),
            mode="lines", fill="toself", fillcolor=cores["regioes"].get(regiao, cores["sem_dado"]),
            line=dict(color=cores["bloco"], width=0.5), hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(
        x=pontos["lon"], y=pontos["lat"], mode="markers",
        marker=dict(**marcador, line=dict(color=cores["bloco"], width=0.6)),
        customdata=pontos["customdata"], hovertemplate=pontos["hover"], **tema.SEM_APAGAR,
    ))

    fig.update_layout(
        **{**tema.base(), "dragmode": "pan"}, height=altura,
        xaxis=dict(visible=False, range=[lon_min, lon_max]),
        # Longe do equador, 1 grau de longitude vale menos que 1 de latitude (cos da latitude)
        yaxis=dict(visible=False, range=[lat_min, lat_max], scaleanchor="x",
                   scaleratio=1 / math.cos(math.radians((lat_min + lat_max) / 2))),
    )
    return fig
