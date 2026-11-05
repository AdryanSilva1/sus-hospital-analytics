import ftplib
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests
from dbfread import DBF
from pyreaddbc import dbc2dbf

from pipeline.config import (CODIGOS_UF, FTP_HOST, FTP_PASTA_SIH, PASTA_BRUTOS,
                             URL_CID10, URL_COORDENADAS, URL_IBGE, URL_MALHA)

# Só as colunas que o projeto usa (o arquivo RD tem mais de 100)
COLUNAS = [
    "ANO_CMPT", "MES_CMPT", "IDENT", "MUNIC_MOV", "SEXO", "RACA_COR",
    "COD_IDADE", "IDADE", "DIAG_PRINC", "PROC_REA", "DIAS_PERM",
    "MORTE", "VAL_TOT",
]


def nome_arquivo(uf, ano, mes):
    # Ex.: SC, 2024, 3 -> RDSC2403.DBC
    return f"RD{uf}{ano % 100:02d}{mes:02d}.DBC"


def _conectar():
    ftp = ftplib.FTP(FTP_HOST, timeout=120)
    ftp.login()
    ftp.cwd(FTP_PASTA_SIH)
    return ftp


def listar_arquivos_disponiveis():
    """Arquivos que existem hoje no FTP.

    Devolve {NOME EM MAIÚSCULO: nome real}, porque o FTP às vezes mistura
    .dbc e .DBC e o download precisa do nome exato.
    """
    with _conectar() as ftp:
        return {nome.upper(): nome for nome in ftp.nlst()}


def baixar_arquivo(arquivo):
    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    destino = PASTA_BRUTOS / arquivo.upper()

    # Se já baixou antes, reaproveita
    if destino.exists():
        return destino

    temporario = destino.with_suffix(".part")
    with _conectar() as ftp, open(temporario, "wb") as f:
        ftp.retrbinary(f"RETR {arquivo}", f.write)
    temporario.rename(destino)

    return destino


def ler_dbc(caminho: Path):
    # .dbc é um .dbf compactado; descompacta, lê e apaga o .dbf
    caminho_dbf = caminho.with_suffix(".dbf")
    dbc2dbf(str(caminho), str(caminho_dbf))

    try:
        tabela = DBF(caminho_dbf, encoding="iso-8859-1", char_decode_errors="ignore")
        df = pd.DataFrame(iter(tabela))
    finally:
        caminho_dbf.unlink(missing_ok=True)

    # Arquivos antigos podem não ter alguma coluna (ex.: RACA_COR)
    for col in COLUNAS:
        if col not in df.columns:
            df[col] = ""

    return df[COLUNAS]


def baixar_municipios(ufs):
    linhas = []
    for uf in ufs:
        resposta = requests.get(URL_IBGE.format(uf=uf), timeout=60)
        resposta.raise_for_status()

        for m in resposta.json():
            linhas.append({
                # IBGE usa 7 dígitos; o SIH usa 6 (sem o dígito verificador)
                "cod_municipio": str(m["id"])[:6],
                "municipio": m["nome"],
                "uf": uf,
            })
    municipios = pd.DataFrame(linhas)

    try:
        coords = pd.read_csv(URL_COORDENADAS, usecols=["codigo_ibge", "latitude", "longitude"])
        coords["cod_municipio"] = coords["codigo_ibge"].astype(str).str[:6]
        municipios = municipios.merge(coords[["cod_municipio", "latitude", "longitude"]],
                                      on="cod_municipio", how="left")
    except Exception as erro:  # o mapa é opcional; sem coordenadas o resto funciona
        print(f"  Aviso: não consegui baixar as coordenadas ({erro})")

    return municipios


def baixar_cid10():
    """Nome de cada categoria da CID-10 (3 caracteres, ex.: J18 -> Pneumonia)."""
    resposta = requests.get(URL_CID10, timeout=120)
    resposta.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resposta.content)) as z:
        arquivo = next(n for n in z.namelist() if n.upper().endswith("CATEGORIAS.CSV"))
        with z.open(arquivo) as f:
            cid = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)

    cid = cid.rename(columns={"CAT": "cid", "DESCRICAO": "descricao"})
    return cid[["cid", "descricao"]]


def baixar_contornos(ufs):
    """Contorno de cada estado como uma lista de pontos (lon, lat).

    Cada polígono vira um 'trecho'; o mapa desenha um trecho por vez.
    """
    linhas = []
    for uf in ufs:
        resposta = requests.get(URL_MALHA.format(codigo=CODIGOS_UF[uf]), timeout=60)
        resposta.raise_for_status()

        for feature in resposta.json()["features"]:
            geometria = feature["geometry"]
            poligonos = geometria["coordinates"]
            if geometria["type"] == "Polygon":
                poligonos = [poligonos]

            for i, poligono in enumerate(poligonos):
                for lon, lat in poligono[0]:  # só o contorno externo
                    linhas.append({"uf": uf, "trecho": f"{uf}-{i}", "lon": lon, "lat": lat})

    return pd.DataFrame(linhas)
