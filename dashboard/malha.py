"""Geometria dos mapas: prepara a malha de municípios do IBGE para o Plotly."""

from collections import Counter, defaultdict

import numpy as np
import pandas as pd


def _area_com_sinal(anel):
    """Positiva quando os pontos giram no sentido anti-horário (fórmula do laço)."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:])) / 2


def _no_sentido_do_plotly(poligono):
    """O mapa do Plotly (d3) espera a borda externa no sentido horário e os buracos ao contrário.

    Sem isso, um polígono no sentido "errado" vira "o mundo inteiro menos o município".
    """
    borda, *buracos = poligono
    if _area_com_sinal(borda) > 0:
        borda = borda[::-1]
    buracos = [b[::-1] if _area_com_sinal(b) < 0 else b for b in buracos]
    return [borda, *buracos]


def _dentro(ponto, anel):
    """Teste do raio: o ponto está dentro do anel?"""
    x, y = ponto
    dentro = False
    for (x1, y1), (x2, y2) in zip(anel, anel[1:]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            dentro = not dentro
    return dentro


def _aneis_da_borda(arestas):
    """Liga as arestas soltas (cada ponto com seus vizinhos) em anéis fechados."""
    vizinhos = defaultdict(list)
    for a, b in arestas:
        vizinhos[a].append(b)
        vizinhos[b].append(a)

    aneis = []
    while vizinhos:
        inicio = next(iter(vizinhos))
        anel, atual = [inicio], inicio
        while vizinhos.get(atual):
            proximo = vizinhos[atual].pop()
            vizinhos[proximo].remove(atual)
            for ponto in (atual, proximo):
                if not vizinhos[ponto]:
                    del vizinhos[ponto]
            anel.append(proximo)
            atual = proximo
        if len(anel) >= 4:
            aneis.append(anel)
    return aneis


def _estados(municipios):
    """Junta os municípios de cada estado num polígono só.

    A malha do IBGE é "encaixada": a divisa entre dois municípios do mesmo estado
    aparece duas vezes (uma em cada um). O que aparece uma vez só é a divisa do estado.
    """
    arestas = defaultdict(Counter)
    for municipio in municipios:
        uf = municipio["properties"]["uf"]
        for poligono in municipio["geometry"]["coordinates"]:
            for anel in poligono:
                for a, b in zip(anel, anel[1:]):
                    a, b = tuple(a), tuple(b)
                    if a != b:
                        arestas[uf][(a, b) if a < b else (b, a)] += 1

    estados = []
    for uf, contagem in arestas.items():
        aneis = _aneis_da_borda([aresta for aresta, n in contagem.items() if n == 1])
        # Anel dentro de outro anel do mesmo estado é buraco (ex.: o DF dentro de Goiás)
        bordas = [a for a in aneis if not any(_dentro(a[0], b) for b in aneis if b is not a)]
        poligonos = [[borda, *[a for a in aneis if a is not borda and _dentro(a[0], borda)]]
                     for borda in bordas]
        estados.append({
            "type": "Feature", "id": uf, "properties": {"uf": uf},
            "geometry": {"type": "MultiPolygon",
                         "coordinates": [_no_sentido_do_plotly(p) for p in poligonos]},
        })
    return {"type": "FeatureCollection", "features": estados}


def _linhas(feature):
    """Bordas de uma feature como x e y, com None entre um anel e outro (um traço só no Plotly)."""
    xs, ys = [], []
    for poligono in feature["geometry"]["coordinates"]:
        for anel in poligono:
            xs.extend([p[0] for p in anel] + [None])
            ys.extend([p[1] for p in anel] + [None])
    return xs, ys


def preparar_malha(geojson):
    """Transforma o GeoJSON do IBGE no que os mapas usam:

    - geojson: o próprio, com todo polígono no sentido que o Plotly espera
    - centros: um ponto (lon, lat) por município, onde fica a bolha
    - contornos: a divisa de cada município, agrupada por estado
    - estados e divisas_por_estado: o mesmo, um polígono por estado (para o Brasil todo)
    """
    centros = []
    contornos = {}

    for municipio in geojson["features"]:
        uf = municipio["properties"]["uf"]
        geometria = municipio["geometry"]
        poligonos = geometria["coordinates"]
        if geometria["type"] == "Polygon":
            poligonos = [poligonos]

        poligonos = [_no_sentido_do_plotly(p) for p in poligonos]
        municipio["geometry"] = {"type": "MultiPolygon", "coordinates": poligonos}

        xs, ys = contornos.setdefault(uf, ([], []))
        for poligono in poligonos:
            borda = poligono[0]
            xs.extend([p[0] for p in borda] + [None])
            ys.extend([p[1] for p in borda] + [None])

        # Centro do maior pedaço do município (média dos pontos da borda)
        maior = max(poligonos, key=lambda p: len(p[0]))[0]
        centros.append({
            "cod_municipio": municipio["id"],
            "lon": sum(p[0] for p in maior) / len(maior),
            "lat": sum(p[1] for p in maior) / len(maior),
        })

    # Em array do numpy (NaN no lugar de None) o Plotly monta a figura bem mais rápido
    contornos = {uf: _em_array(xs, ys) for uf, (xs, ys) in contornos.items()}
    estados = _estados(geojson["features"])
    return {"centros": pd.DataFrame(centros), "contornos": contornos, "geojson": geojson,
            "estados": estados,
            "divisas_por_estado": {e["id"]: _em_array(*_linhas(e)) for e in estados["features"]}}


def _em_array(xs, ys):
    return (np.array(xs, dtype=float), np.array(ys, dtype=float))
