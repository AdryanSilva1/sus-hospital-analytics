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


# Bandeiras simplificadas dos estados (só as cores e formas principais)
_BANDEIRA = '<svg width="54" height="36" viewBox="0 0 30 20" class="bandeira">{}</svg>'
BANDEIRAS = {
    "PR": _BANDEIRA.format(
        '<rect width="30" height="20" fill="#00A859"/>'
        '<polygon points="0,15 0,20 5,20 30,5 30,0 25,0" fill="#FFFFFF"/>'
        '<circle cx="15" cy="10" r="4" fill="#1F4E9E"/>'),
    "SC": _BANDEIRA.format(
        '<rect width="30" height="20" fill="#D52B1E"/>'
        '<rect y="6.6" width="30" height="6.8" fill="#FFFFFF"/>'
        '<polygon points="15,4 20,10 15,16 10,10" fill="#2E8B3A"/>'),
    "RS": _BANDEIRA.format(
        '<polygon points="0,0 22,0 0,15" fill="#00933B"/>'
        '<polygon points="22,0 30,0 30,5 8,20 0,20 0,15" fill="#D52B1E"/>'
        '<polygon points="30,5 30,20 8,20" fill="#F2C400"/>'
        '<circle cx="15" cy="10" r="3.2" fill="#FFFFFF"/>'),
    "Sul": _BANDEIRA.format(
        '<rect width="30" height="20" rx="2" fill="#E7F4F8"/>'
        '<rect x="3" y="3" width="24" height="4" rx="1" fill="#2E86AB"/>'
        '<rect x="3" y="8" width="24" height="4" rx="1" fill="#E4572E"/>'
        '<rect x="3" y="13" width="24" height="4" rx="1" fill="#F3A712"/>'),
}
