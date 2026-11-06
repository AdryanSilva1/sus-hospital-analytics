"""Cores e estilo comuns a todos os gráficos e mapas, no tema claro e no escuro."""

import streamlit as st

from dashboard.brasil import REGIAO_DO_ESTADO
from dashboard.medidas import formatar

# Cada região do Brasil tem uma cor, e os estados usam a cor da sua região.
# Quando algo é clicado, ele fica com a cor e o resto fica cinza (como no Power BI).
CORES_REGIAO = {
    "Norte": "#2A9D8F", "Nordeste": "#F4A261", "Centro-Oeste": "#E9C46A",
    "Sudeste": "#457B9D", "Sul": "#E76F51",
}
CORES_ESTADO = {uf: CORES_REGIAO[regiao] for uf, regiao in REGIAO_DO_ESTADO.items()}

# Para as regiões do IBGE dentro de um estado (que mudam de estado para estado)
PALETA = ["#3A9BBF", "#E76F51", "#E9C46A", "#2A9D8F", "#9C7BC0", "#F4A261", "#457B9D",
          "#6BBF8A", "#D16BA5", "#5DA9E9", "#B08968", "#8AB17D"]

TEMAS = {
    "light": {
        "barra": "#3A86C4", "apagado": "#D9DCE1", "forte": "#1F4E79", "fraco": "#71717A",
        "destaque": "#1F4E79", "anterior": "#B4B4BC",
        "obito": "#DC2626", "bloco": "#FFFFFF", "borda": "#E4E4E7", "grade": "#F0F0F2",
        "sem_dado": "#F0F0F2", "ruas": "carto-positron",
        "escala": [[0, "#E3EEF8"], [0.35, "#8DBFE3"], [0.7, "#3A86C4"], [1, "#123A63"]],
        "regioes": {"Norte": "#DCEDE7", "Nordeste": "#F5E6D6", "Centro-Oeste": "#F2EDD3",
                    "Sudeste": "#DDE5EF", "Sul": "#F0DEDB"},
    },
    "dark": {
        "barra": "#5DA9E9", "apagado": "#3A3A40", "forte": "#93C5FD", "fraco": "#A1A1AA",
        "destaque": "#BFDBFE", "anterior": "#52525B",
        "obito": "#F87171", "bloco": "#161618", "borda": "#2E2E33", "grade": "#232327",
        "sem_dado": "#1F1F23", "ruas": "carto-darkmatter",
        "escala": [[0, "#1E2A3A"], [0.35, "#2F5D8A"], [0.7, "#5DA9E9"], [1, "#DBEAFE"]],
        "regioes": {"Norte": "#1E302B", "Nordeste": "#33291F", "Centro-Oeste": "#302D1E",
                    "Sudeste": "#1F2733", "Sul": "#332322"},
    },
}

CONFIG = {"displayModeBar": False}

# Sem isso o Plotly apaga as barras que não foram clicadas
SEM_APAGAR = dict(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)))


def atual():
    return TEMAS["dark" if st.context.theme.type == "dark" else "light"]


def base():
    # A cor do texto e da grade fica com o tema do Streamlit, que acompanha o claro/escuro
    tema = atual()
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13),
        separators=",.",
        hoverlabel=dict(bgcolor=tema["bloco"], bordercolor=tema["borda"], font_size=13,
                        font_color=tema["forte"]),
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        clickmode="event+select",
        dragmode=False,
    )


def dica_clique():
    return f"<span style='color:{atual()['fraco']}'>clique para filtrar</span>"


def texto(valores, medida, formatador):
    formatador = formatador or (lambda v: formatar(v, medida))
    return [formatador(v) for v in valores]


def cores_das_regioes(nomes):
    """Uma cor da PALETA para cada região do IBGE, na ordem em que aparecem."""
    return {nome: PALETA[i % len(PALETA)] for i, nome in enumerate(dict.fromkeys(nomes))}


def com_destaque(chaves, selecionado, cores=None):
    """Cor de cada item: a do seu grupo (ou a padrão); com algo clicado, o resto fica cinza."""
    tema = atual()
    cores = list(cores) if cores is not None else [tema["barra"]] * len(chaves)
    if selecionado is None:
        return cores
    return [cor if k == selecionado else tema["apagado"] for k, cor in zip(chaves, cores)]


def cores_do_grupo(dados, cor):
    """`cor`: None (cor padrão), "uf" (cor da região do estado) ou (coluna, {valor: cor})."""
    if cor is None:
        return None
    coluna, mapa_cores = (cor, CORES_ESTADO) if cor == "uf" else cor
    return [mapa_cores.get(v, atual()["barra"]) for v in dados[coluna]]
