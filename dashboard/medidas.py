"""Medidas do painel (internações, óbitos, valor...) e formatação no padrão brasileiro."""

import pandas as pd

METRICAS = ["internacoes", "obitos", "valor_total", "dias_internado"]

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

# Em médias e porcentagens, item com poucas internações distorce o ranking
MINIMO_PARA_RAZAO = 50


def eh_razao(medida):
    return MEDIDAS[medida][1] is not None


def _razao(numerador, denominador, formato):
    valor = numerador / denominador
    return valor * 100 if formato == "porcentagem" else valor


def somar(df, por, colunas=METRICAS):
    """Soma `colunas` por `por`. As colunas de categoria voltam a ser texto simples,
    para o resultado aceitar contas como municipio + " (SC)"."""
    grupo = df.groupby(por, observed=True)[colunas].sum().reset_index()
    for coluna in por:
        if isinstance(grupo[coluna].dtype, pd.CategoricalDtype):
            grupo[coluna] = grupo[coluna].astype(str)
    return grupo


def calcular(df, por, medida):
    """Agrupa por `por` e cria a coluna `valor` com a medida escolhida."""
    numerador, denominador, formato = MEDIDAS[medida]
    grupo = somar(df, por)

    if denominador:
        grupo = grupo[grupo[denominador] > 0]
        grupo["valor"] = _razao(grupo[numerador], grupo[denominador], formato)
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
    return _razao(soma[numerador], soma[denominador], formato)


def tirar_pequenos(df, medida):
    if eh_razao(medida):
        return df[df["internacoes"] >= MINIMO_PARA_RAZAO]
    return df


def por_100_mil(internacoes, populacao):
    return internacoes / populacao * 100_000


# ── Formatação ───────────────────────────────────────────────

def numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def decimal(valor):
    return f"{valor:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def porcentagem(valor):
    return f"{valor:.2f}%".replace(".", ",")


def reais(valor):
    if valor >= 1e9:
        return f"R$ {valor / 1e9:.2f} bi".replace(".", ",")
    if valor >= 1e6:
        return f"R$ {valor / 1e6:.1f} mi".replace(".", ",")
    return "R$ " + numero(valor)


FORMATOS = {"numero": numero, "decimal": decimal, "porcentagem": porcentagem, "reais": reais}


def formatar(valor, medida):
    return FORMATOS[MEDIDAS[medida][2]](valor)


def variacao(atual, anterior):
    """Texto da variação percentual, ex.: '▲ 3,2%'. None quando não dá para comparar."""
    if not anterior:
        return None
    mudanca = (atual - anterior) / anterior * 100
    seta = "▲" if mudanca > 0 else "▼" if mudanca < 0 else "="
    return f"{seta} {abs(mudanca):.1f}%".replace(".", ",")
