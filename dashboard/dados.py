"""Leitura das tabelas do pipeline e recorte pelos filtros do painel."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.malha import preparar_malha

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


@st.cache_resource
def carregar():
    """Lê as tabelas geradas pelo pipeline. O painel nunca busca dado no DATASUS.

    cache_resource (e não cache_data) porque com o Brasil todo são ~300 MB na memória:
    o cache_data faz uma cópia a cada clique. As tabelas são só lidas, nunca alteradas.
    """
    tabelas = {nome: _ler_pasta(f"por_{nome}") for nome in TABELAS}

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
    for nome in TABELAS:
        tabelas[nome] = _compactar(tabelas[nome])
    tabelas["populacao"] = _ler_opcional("populacao.parquet")

    arq_malha = PASTA / "municipios.geojson"
    tabelas["malha"] = None
    if arq_malha.exists():
        tabelas["malha"] = preparar_malha(json.loads(arq_malha.read_text(encoding="utf-8")))

    return tabelas, _ler_pasta("controle")


def _compactar(df):
    """Texto vira categoria e número inteiro vira int32: a memória cai para cerca de 1/4.

    Com o Brasil todo eram ~320 MB e o painel caía em máquina com pouca RAM.
    Colunas que são comparadas entre si (onde mora × onde foi internado) dividem
    as mesmas categorias, senão o pandas não deixa comparar.
    """
    df = df.copy()
    pares = [("cod_residencia", "cod_municipio"), ("residencia", "municipio")]
    for a, b in pares:
        if a in df and b in df:
            tipo = pd.CategoricalDtype(sorted(set(df[a].dropna()) | set(df[b].dropna())))
            df[a], df[b] = df[a].astype(tipo), df[b].astype(tipo)
    for coluna in df.columns:
        tipo = df[coluna].dtype
        if tipo == "int64":
            df[coluna] = df[coluna].astype("int32")
        elif not isinstance(tipo, pd.CategoricalDtype) and pd.api.types.is_string_dtype(tipo):
            df[coluna] = df[coluna].astype("category")
    return df


def _ler_pasta(pasta):
    """Junta os arquivos de todos os estados (ex.: por_municipio/SC.parquet, PR.parquet...)."""
    arquivos = sorted((PASTA / pasta).glob("*.parquet"))
    if not arquivos:
        raise FileNotFoundError(PASTA / pasta)
    return pd.concat([pd.read_parquet(a) for a in arquivos], ignore_index=True)


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
    # Código de município que o IBGE não tem (ex.: ignorado ou de outro país)
    df[coluna_nome] = df[coluna_nome].fillna("Não informado")
    return df


def _com_descricao_cid(cid):
    descricoes = _ler_opcional("cid10.parquet")
    if descricoes is not None:
        cid = cid.merge(descricoes, on="cid", how="left")
    if "descricao" not in cid:
        cid["descricao"] = None
    cid["descricao"] = cid["descricao"].fillna("—")
    return cid


def recorte(tabelas, nome, filtros, ignorar=()):
    """Aplica na tabela `nome` os filtros que ela tem.

    `ignorar` serve para o gráfico de uma dimensão mostrar todos os itens
    dela (e só destacar o escolhido), como no Power BI.
    """
    df = tabelas[nome]
    # O ano primeiro: é o filtro que mais corta linhas, e os outros ficam mais rápidos
    for coluna, valor in sorted(filtros.items(), key=lambda item: item[0] != "ano"):
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
