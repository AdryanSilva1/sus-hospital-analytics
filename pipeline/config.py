from pathlib import Path

# Estados da Região Sul
UFS = ["PR", "SC", "RS"]

# Primeiro ano que o pipeline busca
ANO_INICIAL = 2019

# FTP oficial do DATASUS — SIH/SUS, arquivos RD (AIH reduzida)
FTP_HOST = "ftp.datasus.gov.br"
FTP_PASTA_SIH = "/dissemin/publicos/SIHSUS/200801_/Dados"

# Tabela oficial da CID-10 publicada pelo DATASUS
URL_CID10 = "http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip"

# Nomes dos municípios: API oficial do IBGE
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"

# Contorno dos estados: API oficial de malhas do IBGE (usado só no mapa)
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/{codigo}"
             "?formato=application/vnd.geo+json&qualidade=minima")
CODIGOS_UF = {"PR": 41, "SC": 42, "RS": 43}

# Coordenadas dos municípios (base aberta montada a partir do IBGE), usadas só no mapa
URL_COORDENADAS = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BRUTOS = RAIZ / "data" / "brutos"
PASTA_PROCESSADOS = RAIZ / "data" / "processados"

ARQ_MUNICIPIOS = PASTA_PROCESSADOS / "municipios.parquet"
ARQ_CID10 = PASTA_PROCESSADOS / "cid10.parquet"
ARQ_CONTORNOS = PASTA_PROCESSADOS / "contornos.parquet"
ARQ_CONTROLE = PASTA_PROCESSADOS / "controle.parquet"

# Uma tabela por visual do painel, todas resumidas por ano
TABELAS = {
    "municipio": PASTA_PROCESSADOS / "por_municipio.parquet",
    "perfil": PASTA_PROCESSADOS / "por_perfil.parquet",
    "cid": PASTA_PROCESSADOS / "por_cid.parquet",
}
