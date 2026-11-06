"""Estados e regiões do Brasil, e o que cada escolha do seletor de local quer dizer."""

from pipeline.config import CODIGOS_UF

REGIOES = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}

ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}

# Uma cor por região do Brasil; os estados usam a cor da sua região
CORES_REGIAO = {
    "Norte": "#2A9D8F", "Nordeste": "#F4A261", "Centro-Oeste": "#E9C46A",
    "Sudeste": "#457B9D", "Sul": "#E76F51",
}
REGIAO_DO_ESTADO = {uf: regiao for regiao, ufs in REGIOES.items() for uf in ufs}
CORES_ESTADO = {uf: CORES_REGIAO[regiao] for uf, regiao in REGIAO_DO_ESTADO.items()}

# Do código IBGE do município (2 primeiros dígitos) para a sigla do estado
ESTADO_DO_CODIGO = {str(codigo): uf for uf, codigo in CODIGOS_UF.items()}

# Opções do seletor de local: o país, as cinco regiões e os 27 estados
LOCAIS = ["Brasil", *REGIOES, *sorted(ESTADOS)]


def estados_do_local(local):
    """Lista de siglas que um local do seletor cobre."""
    if local == "Brasil":
        return sorted(ESTADOS)
    return REGIOES.get(local, [local])


def nome_do_local(local):
    if local in ESTADOS:
        return ESTADOS[local]
    return "Brasil" if local == "Brasil" else f"Região {local}"


def e_um_estado(local):
    return local in ESTADOS
