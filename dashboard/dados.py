from pathlib import Path

import pandas as pd
import streamlit as st

PASTA = Path(__file__).resolve().parent.parent / "data" / "processados"

METRICAS = ["internacoes", "obitos", "valor_total", "dias_internado"]

# Ícone de cada sistema do corpo (capítulo da CID-10)
ICONES_SISTEMA = {
    "Circulatório": "🫀", "Digestivo": "🍽️", "Respiratório": "🫁",
    "Geniturinário": "🫘", "Músculo/Osso": "🦴", "Neoplasias": "🎗️",
    "Saúde Mental": "💭", "Sistema Nervoso": "🧠", "Gravidez e Parto": "🤰",
    "Lesões": "🩹", "Infecciosas": "🦠", "Olhos": "👁️", "Ouvido": "👂",
    "Pele/Tecido": "✋", "Endócrinas": "🧪", "Sangue": "🩸", "Perinatal": "👶",
    "Malformações": "🧬", "Sintomas": "🌡️", "COVID e especiais": "😷",
    "Causas Externas": "🚑", "Outros Contatos": "📋", "Não informado": "❔",
}

# Os que aparecem como botão no topo do painel
SISTEMAS_BOTOES = [
    "Circulatório", "Digestivo", "Respiratório", "Geniturinário", "Músculo/Osso",
    "Neoplasias", "Gravidez e Parto", "Lesões", "Saúde Mental", "Sistema Nervoso",
    "Infecciosas", "Olhos",
]


@st.cache_data
def carregar():
    """Lê as tabelas geradas pelo pipeline. O painel nunca busca dado no DATASUS."""
    tabelas = {
        nome: pd.read_parquet(PASTA / f"por_{nome}.parquet")
        for nome in ["municipio", "perfil", "cid"]
    }

    municipios = pd.read_parquet(PASTA / "municipios.parquet")
    tabelas["municipio"] = tabelas["municipio"].merge(
        municipios.drop(columns="uf"), on="cod_municipio", how="left"
    )
    tabelas["municipio"]["municipio"] = tabelas["municipio"]["municipio"].fillna("Não identificado")

    arq_cid = PASTA / "cid10.parquet"
    if arq_cid.exists():
        tabelas["cid"] = tabelas["cid"].merge(pd.read_parquet(arq_cid), on="cid", how="left")
    if "descricao" not in tabelas["cid"]:
        tabelas["cid"]["descricao"] = None
    tabelas["cid"]["descricao"] = tabelas["cid"]["descricao"].fillna("—")

    # Fundo do mapa: todos os municípios (pontinhos cinza) e o contorno dos estados
    tabelas["fundo"] = municipios.dropna(subset=["latitude", "longitude"]) if "latitude" in municipios else None
    arq_contornos = PASTA / "contornos.parquet"
    tabelas["contornos"] = pd.read_parquet(arq_contornos) if arq_contornos.exists() else None

    controle = pd.read_parquet(PASTA / "controle.parquet")
    return tabelas, controle


def filtrar(df, **filtros):
    """Aplica só os filtros que existem na tabela e que não estão em 'Todos'."""
    for coluna, valor in filtros.items():
        if valor in (None, "Todos") or coluna not in df.columns:
            continue
        df = df[df[coluna].isin(valor) if isinstance(valor, list) else df[coluna] == valor]
    return df


# ── Medidas (o seletor da direita) ───────────────────────────
# nome: (numerador, denominador, como formatar)
MEDIDAS = {
    "Internações": ("internacoes", None, "numero"),
    "Dias": ("dias_internado", None, "numero"),
    "Dias por Internação": ("dias_internado", "internacoes", "decimal"),
    "Óbitos": ("obitos", None, "numero"),
    "Porcentagem de Óbitos": ("obitos", "internacoes", "porcentagem"),
    "Valor AIH": ("valor_total", None, "reais"),
    "Valor Médio AIH": ("valor_total", "internacoes", "reais"),
}

ICONES_MEDIDA = {
    "Internações": "🛏️", "Dias": "📅", "Dias por Internação": "⏳", "Óbitos": "🕊️",
    "Porcentagem de Óbitos": "📉", "Valor AIH": "💵", "Valor Médio AIH": "🧾",
}

# Em medidas de razão, município com poucas internações distorce o ranking
MINIMO_PARA_RAZAO = 50


def eh_razao(medida):
    return MEDIDAS[medida][1] is not None


def calcular(df, por, medida):
    """Agrupa por 'por' e devolve a coluna 'valor' com a medida escolhida."""
    numerador, denominador, formato = MEDIDAS[medida]
    grupo = df.groupby(por, observed=True)[METRICAS].sum().reset_index()

    if denominador:
        grupo = grupo[grupo[denominador] > 0]
        grupo["valor"] = grupo[numerador] / grupo[denominador]
        if formato == "porcentagem":
            grupo["valor"] *= 100
    else:
        grupo["valor"] = grupo[numerador]

    return grupo.sort_values("valor", ascending=False)


def total(df, medida):
    numerador, denominador, formato = MEDIDAS[medida]
    soma = df[METRICAS].sum()

    if not denominador:
        return soma[numerador]
    if soma[denominador] == 0:
        return 0
    valor = soma[numerador] / soma[denominador]
    return valor * 100 if formato == "porcentagem" else valor


# ── Formatação no padrão brasileiro ──────────────────────────

def numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def decimal(valor):
    return f"{valor:.1f}".replace(".", ",")


def porcentagem(valor):
    return f"{valor:.2f}%".replace(".", ",")


def reais(valor):
    if valor >= 1e9:
        return f"R$ {valor / 1e9:.2f} bi".replace(".", ",")
    if valor >= 1e6:
        return f"R$ {valor / 1e6:.1f} mi".replace(".", ",")
    return "R$ " + numero(valor)


def formatar(valor, medida):
    funcoes = {"numero": numero, "decimal": decimal, "porcentagem": porcentagem, "reais": reais}
    return funcoes[MEDIDAS[medida][2]](valor)
