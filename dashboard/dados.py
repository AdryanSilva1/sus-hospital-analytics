"""Leitura das tabelas do pipeline e recorte pelos filtros do painel."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PASTA = Path(__file__).resolve().parent.parent / "data" / "processados"

TABELAS = ["municipio", "perfil", "cid", "mes", "fluxo"]

# Filtros que só existem numa tabela (os demais existem em todas)
TABELA_DO_FILTRO = {
    "regiao": "municipio",
    "cod_municipio": "municipio",
    "cid": "cid",
    "sexo": "perfil",
    "faixa_etaria": "perfil",
    "raca": "perfil",
}


@st.cache_data
def carregar():
    """Lê as tabelas geradas pelo pipeline. O painel nunca busca dado no DATASUS."""
    tabelas = {nome: pd.read_parquet(PASTA / f"por_{nome}.parquet") for nome in TABELAS}

    municipios = _municipios(tabelas["municipio"])
    nomes = municipios[["cod_municipio", "municipio"]]

    tabelas["municipio"] = _com_nome(tabelas["municipio"], nomes, "cod_municipio", "municipio")
    tabelas["municipio"] = tabelas["municipio"].merge(
        municipios[["cod_municipio", "regiao"]], on="cod_municipio", how="left")
    tabelas["municipio"]["regiao"] = tabelas["municipio"]["regiao"].fillna("Sem região")
    tabelas["fluxo"] = _com_nome(tabelas["fluxo"], nomes, "cod_municipio", "municipio")
    tabelas["fluxo"] = _com_nome(tabelas["fluxo"], nomes, "cod_residencia", "residencia")
    tabelas["municipios"] = municipios

    tabelas["cid"] = _com_descricao_cid(tabelas["cid"])
    tabelas["populacao"] = _ler_opcional("populacao.parquet")

    arq_malha = PASTA / "municipios.geojson"
    tabelas["malha"] = None
    if arq_malha.exists():
        tabelas["malha"] = preparar_malha(json.loads(arq_malha.read_text(encoding="utf-8")))

    controle = pd.read_parquet(PASTA / "controle.parquet")
    return tabelas, controle


def _municipios(por_municipio):
    """Nome e região de cada município, do IBGE.

    Sem o arquivo (a API do IBGE só responde no Brasil), o painel mostra o código
    do município e usa o estado como região, para não ficar fora do ar.
    """
    municipios = _ler_opcional("municipios.parquet")
    if municipios is None:
        codigos = por_municipio[["cod_municipio", "uf"]].drop_duplicates()
        return codigos.assign(municipio="Município " + codigos["cod_municipio"], regiao=codigos["uf"])
    if "regiao" not in municipios:  # dados de uma versão antiga do pipeline
        municipios["regiao"] = municipios["uf"]
    return municipios


def _ler_opcional(arquivo):
    caminho = PASTA / arquivo
    return pd.read_parquet(caminho) if caminho.exists() else None


def _com_nome(df, nomes, coluna_codigo, coluna_nome):
    nomes = nomes.rename(columns={"cod_municipio": coluna_codigo, "municipio": coluna_nome})
    df = df.merge(nomes, on=coluna_codigo, how="left")
    # Quem mora fora do PR, SC e RS não está na lista de municípios
    df[coluna_nome] = df[coluna_nome].fillna("Fora da Região Sul / não informado")
    return df


def _com_descricao_cid(cid):
    descricoes = _ler_opcional("cid10.parquet")
    if descricoes is not None:
        cid = cid.merge(descricoes, on="cid", how="left")
    if "descricao" not in cid:
        cid["descricao"] = None
    cid["descricao"] = cid["descricao"].fillna("—")
    return cid


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


def preparar_malha(geojson):
    """Transforma o GeoJSON do IBGE no que o mapa usa (além do próprio GeoJSON):

    - centros: um ponto (lon, lat) por município, onde fica a bolha
    - contornos: as divisas de cada estado como uma lista de pontos,
      com None separando um município do outro (o Plotly desenha tudo num traço só)
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

    return {"centros": pd.DataFrame(centros), "contornos": contornos, "geojson": geojson}


def recorte(tabelas, nome, filtros, ignorar=()):
    """Aplica na tabela `nome` os filtros que ela tem.

    `ignorar` serve para o gráfico de uma dimensão mostrar todos os itens
    dela (e só destacar o escolhido), como no Power BI.
    """
    df = tabelas[nome]
    for coluna, valor in filtros.items():
        if coluna in ignorar or coluna not in df.columns or valor in (None, "Todos"):
            continue
        df = df[df[coluna].isin(valor)] if isinstance(valor, list) else df[df[coluna] == valor]
    return df


def tabela_principal(filtros):
    """Tabela que responde pelos números do topo, conforme o filtro de foco escolhido."""
    for coluna, nome in TABELA_DO_FILTRO.items():
        if filtros.get(coluna):
            return nome
    return "municipio"


def filtros_fora(nome, filtros):
    """Filtros escolhidos que a tabela `nome` não consegue aplicar."""
    return [c for c, t in TABELA_DO_FILTRO.items() if filtros.get(c) and t != nome]
