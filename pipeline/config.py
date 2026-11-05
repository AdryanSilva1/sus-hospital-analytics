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

# Contorno de cada município: API oficial de malhas do IBGE (usado só no mapa)
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/{codigo}"
             "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio")
CODIGOS_UF = {"PR": 41, "SC": 42, "RS": 43}

# População residente do Censo 2022 (IBGE, agregado 4709, variável 93), por município
URL_POPULACAO = ("https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022"
                 "/variaveis/93?localidades=N6[N3[{codigos}]]")

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BRUTOS = RAIZ / "data" / "brutos"
PASTA_PROCESSADOS = RAIZ / "data" / "processados"

ARQ_MUNICIPIOS = PASTA_PROCESSADOS / "municipios.parquet"
ARQ_CID10 = PASTA_PROCESSADOS / "cid10.parquet"
ARQ_MALHA = PASTA_PROCESSADOS / "municipios.geojson"
ARQ_POPULACAO = PASTA_PROCESSADOS / "populacao.parquet"
ARQ_CONTROLE = PASTA_PROCESSADOS / "controle.parquet"

# Uma tabela por visual do painel, todas resumidas por ano
TABELAS = {
    "municipio": PASTA_PROCESSADOS / "por_municipio.parquet",
    "perfil": PASTA_PROCESSADOS / "por_perfil.parquet",
    "cid": PASTA_PROCESSADOS / "por_cid.parquet",
    "mes": PASTA_PROCESSADOS / "por_mes.parquet",
    "fluxo": PASTA_PROCESSADOS / "por_fluxo.parquet",
}
