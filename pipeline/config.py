from pathlib import Path

# Código IBGE de cada estado e a região do Brasil de cada um
CODIGOS_UF = {
    "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29,
    "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
    "PR": 41, "SC": 42, "RS": 43,
    "MS": 50, "MT": 51, "GO": 52, "DF": 53,
}
UFS = list(CODIGOS_UF)

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
# As tabelas resumidas ficam numa pasta cada, com um arquivo por estado
# (ex.: por_municipio/SC.parquet). Assim vários estados podem ser processados
# ao mesmo tempo, em jobs separados, sem um mexer no arquivo do outro.
TABELAS = ["municipio", "perfil", "cid", "mes", "fluxo", "controle"]


def arquivo_da_tabela(nome, uf):
    pasta = "controle" if nome == "controle" else f"por_{nome}"
    return PASTA_PROCESSADOS / pasta / f"{uf}.parquet"
