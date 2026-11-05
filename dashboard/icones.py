"""Ícones (emoji) de cada sistema do corpo e de cada medida."""

SISTEMAS = {
    "Circulatório": "🫀", "Digestivo": "🍽️", "Respiratório": "🫁", "Geniturinário": "🫘",
    "Músculo/Osso": "🦴", "Neoplasias": "🎗️", "Saúde Mental": "💭", "Sistema Nervoso": "🧠",
    "Gravidez e Parto": "🤰", "Lesões": "🩹", "Infecciosas": "🦠", "Olhos": "👁️",
    "Ouvido": "👂", "Pele/Tecido": "🖐️", "Endócrinas": "🧪", "Sangue": "🩸",
    "Perinatal": "👶", "Malformações": "🧬", "Sintomas": "🌡️", "COVID e especiais": "😷",
    "Causas Externas": "🚑", "Outros Contatos": "📋", "Não informado": "❔",
}

# Os que viram botão no topo do painel, nessa ordem
BOTOES = ["Circulatório", "Digestivo", "Respiratório", "Geniturinário", "Músculo/Osso",
          "Neoplasias", "Gravidez e Parto", "Lesões", "Saúde Mental", "Sistema Nervoso",
          "Olhos", "Pele/Tecido"]

MEDIDAS = {
    "Internações": "🛏️", "Dias": "📅", "Dias por Internação": "⏳", "Óbitos": "🕊️",
    "Porcentagem de Óbitos": "📉", "Valor AIH": "💵", "Valor Médio AIH": "🧾",
}


def sistema(nome):
    return SISTEMAS.get(nome, "•")
