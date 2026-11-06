"""Ícones de traço (SVG 24x24) de cada sistema do corpo, de cada medida e dos cartões."""

from urllib.parse import quote

# Cor do ícone de cada botão de sistema, repetindo nessa ordem (mesma paleta dos gráficos)
CORES_DOS_ICONES = ["#3A86C4", "#E76F51", "#2A9D8F", "#F4A261", "#457B9D", "#E9C46A"]

SISTEMAS = {
    "Circulatório":
        '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>'
        '<path d="M7.5 12h2.5l1.2-2 1.8 4 1.2-2h2.3"/>',
    "Digestivo":
        '<path d="M7 3v18M5 3v5a2 2 0 0 0 4 0V3M17 21V3c-2.2 1.2-3.5 4-3.5 7.5V13H17"/>',
    "Respiratório":
        '<path d="M12 3v8l-2.5 2M12 11l2.5 2"/>'
        '<path d="M9 7.5C5.8 7.5 4 12 4 16.5 4 19 5 20 6.8 20 8.6 20 9.5 19 9.5 17v-6"/>'
        '<path d="M15 7.5c3.2 0 5 4.5 5 9 0 2.5-1 3.5-2.8 3.5-1.8 0-2.7-1-2.7-3v-6"/>',
    "Geniturinário":
        '<path d="M15 4c-4.5 0-8.5 3.4-8.5 8.2 0 4.6 3.2 7.8 7 7.8 2.7 0 4-1.7 4-3.6'
        ' 0-1.8-1.8-2.7-1.8-4.2 0-1.6 2.3-2.2 2.3-4.4C18 5.4 16.8 4 15 4z"/>',
    "Músculo/Osso":
        '<path d="M8.5 15.5l7-7"/><circle cx="6.5" cy="14.5" r="2"/>'
        '<circle cx="9.5" cy="17.5" r="2"/><circle cx="14.5" cy="6.5" r="2"/>'
        '<circle cx="17.5" cy="9.5" r="2"/>',
    "Neoplasias":
        '<path d="M12 3a3 3 0 0 0-3 3c0 3 6 8 6 15M12 3a3 3 0 0 1 3 3c0 3-6 8-6 15"/>',
    "Saúde Mental":
        '<path d="M7 16.5a4 4 0 0 1-.4-8 5 5 0 0 1 9.6-1.4 4 4 0 0 1 1.3 9.4z"/>'
        '<circle cx="8" cy="20" r="1.2"/>',
    "Sistema Nervoso":
        '<path d="M12 5a3 3 0 0 0-5.5 1.5A3 3 0 0 0 5 12a3 3 0 0 0 2 5 3 3 0 0 0 5 1.5z"/>'
        '<path d="M12 5a3 3 0 0 1 5.5 1.5A3 3 0 0 1 19 12a3 3 0 0 1-2 5 3 3 0 0 1-5 1.5z"/>'
        '<path d="M12 5v13.5"/>',
    "Gravidez e Parto":
        '<circle cx="11" cy="5" r="2.2"/>'
        '<path d="M11 8.5c-1.8 0-2.8 1.6-2.8 4V21'
        'M11 8.5c2 0 3 1.8 3.8 4.4.8 2.8-.6 4.6-3.3 4.6H10"/>',
    "Lesões":
        '<rect x="3" y="8.5" width="18" height="7" rx="3.5" transform="rotate(-45 12 12)"/>'
        '<path d="M10.5 10.5h.01M13.5 13.5h.01M13.5 10.5h.01M10.5 13.5h.01"/>',
    "Infecciosas":
        '<circle cx="12" cy="12" r="5"/>'
        '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.9 2.9'
        'M15.5 15.5l2.9 2.9M5.6 18.4l2.9-2.9M15.5 8.5l2.9-2.9"/>',
    "Olhos":
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/>'
        '<circle cx="12" cy="12" r="3"/>',
    "Ouvido":
        '<path d="M7 9a5 5 0 0 1 10 0c0 3-3 4-3 7a3 3 0 0 1-6 0"/>'
        '<path d="M10 9a2 2 0 0 1 4 0c0 1.5-2 2-2 3.5"/>',
    "Pele/Tecido":
        '<path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V11M11 10V4.5a1.5 1.5 0 0 1 3 0V11'
        'M14 10.5V6a1.5 1.5 0 0 1 3 0v8a7 7 0 0 1-7 7h-.5a6 6 0 0 1-5-2.7'
        'L3 16a1.5 1.5 0 0 1 2.5-1.7L8 17"/>',
    "Endócrinas":
        '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3M7.5 15h9"/>',
    "Sangue":
        '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "Perinatal":
        '<circle cx="12" cy="12" r="8.5"/>'
        '<path d="M9.5 10.5h.01M14.5 10.5h.01M9.5 14.5a3.5 3.5 0 0 0 5 0"/>',
    "Malformações":
        '<path d="M7 3c0 6 10 6 10 12 0 3-1 4.5-2 6M17 3c0 6-10 6-10 12 0 3 1 4.5 2 6'
        'M8.5 7h7M8.5 17h7"/>',
    "Sintomas":
        '<path d="M14 14.5V5a2 2 0 0 0-4 0v9.5a4 4 0 1 0 4 0z"/><path d="M12 9v6.5"/>',
    "COVID e especiais":
        '<path d="M4 9c3-1 5-2 8-2s5 1 8 2v4c0 3-4 5-8 5s-8-2-8-5z"/>'
        '<path d="M4 10H2.5v2c0 1 .7 2 1.8 2.3M20 10h1.5v2c0 1-.7 2-1.8 2.3'
        'M9 11h6M9 14h6"/>',
    "Causas Externas":
        '<path d="M7 18v-6a5 5 0 0 1 10 0v6M5 18h14v3H5z'
        'M12 3v2M4.2 6.2l1.4 1.4M19.8 6.2l-1.4 1.4"/>',
    "Outros Contatos":
        '<rect x="5" y="4" width="14" height="17" rx="2"/>'
        '<path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h4"/>',
    "Não informado":
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17.5h.01"/>',
}

# Os que viram botão no topo do painel, nessa ordem
BOTOES = ["Circulatório", "Digestivo", "Respiratório", "Geniturinário", "Músculo/Osso",
          "Neoplasias", "Gravidez e Parto", "Lesões", "Saúde Mental", "Sistema Nervoso",
          "Olhos", "Pele/Tecido"]

_CALENDARIO = ('<rect x="3.5" y="5" width="17" height="15.5" rx="2"/>'
               '<path d="M3.5 10h17M8 3v4M16 3v4"/>')
_NOTA = ('<rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>'
         '<path d="M6 12h.01M18 12h.01"/>')
_RECIBO = '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>'

MEDIDAS = {
    "Internações":
        '<path d="M3 6v13M3 16h18v3M21 16v-4a3 3 0 0 0-3-3h-7v7"/><circle cx="7" cy="11.5" r="2"/>',
    "Dias": _CALENDARIO,
    "Dias por Internação": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "Óbitos":
        '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>'
        '<path d="M3 3l18 18"/>',
    "Porcentagem de Óbitos":
        '<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>',
    "Valor AIH": _NOTA,
    "Valor Médio AIH": _RECIBO,
}

# Ícones dos cartões das páginas de gastos e de fluxo
CARTOES = {
    "gasto": _NOTA,
    "recibo": _RECIBO,
    "calendario": _CALENDARIO,
    "cirurgia":
        '<path d="M5 3v6a5 5 0 0 0 10 0V3"/><path d="M10 14v2a5 5 0 0 0 10 0v-2"/>'
        '<circle cx="20" cy="12" r="2"/>',
    "hospital":
        '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M12 7v6M9 10h6M9 21v-4h6v4"/>',
    "cidade": '<path d="M3 21h18M5 21V8l5-3v16M10 21V10h9v11M13 13h3M13 17h3"/>',
    "mapa": '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14"/>',
    "carro":
        '<path d="M4 16h16v-3l-2-4H6l-2 4z"/>'
        '<circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/>',
    "saida": '<path d="M7 17L17 7M9 7h8v8"/>',
    "atualizado": _CALENDARIO + '<path d="M9 15l2 2 4-4"/>',
}

# O xmlns é obrigatório quando o SVG vira imagem (máscara do CSS)
_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" class="icone" width="{tamanho}" height="{tamanho}" '
        'viewBox="0 0 24 24" fill="none" '
        'stroke="{cor}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '{desenho}</svg>')


def svg(desenho, tamanho=24):
    """SVG pronto para colocar no HTML; pega a cor do texto em volta."""
    return _SVG.format(tamanho=tamanho, cor="currentColor", desenho=desenho)


def sistema(nome):
    return svg(SISTEMAS.get(nome, SISTEMAS["Não informado"]), 18)


def _mascara(desenho):
    # Botões e opções do Streamlit não aceitam SVG, então o ícone entra
    # pelo CSS como máscara e é pintado com a cor do texto
    return f'url("data:image/svg+xml,{quote(_SVG.format(tamanho=24, cor="black", desenho=desenho))}")'


def css():
    """Regras CSS que põem o ícone em cada botão de sistema e em cada opção de medida."""
    regras = [f".st-key-sistema-{i} button {{ --icone: {_mascara(SISTEMAS[nome])}; "
              f"--cor-icone: {CORES_DOS_ICONES[i % len(CORES_DOS_ICONES)]}; }}"
              for i, nome in enumerate(BOTOES)]
    opcao = ".st-key-tile-medidas label[data-baseweb='radio']"
    regras += [f"{opcao}:nth-of-type({i}) {{ --icone: {_mascara(desenho)}; }}"
               for i, desenho in enumerate(MEDIDAS.values(), start=1)]
    return "\n".join(regras)


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
    "Brasil": _BANDEIRA.format(
        '<rect width="30" height="20" fill="#009C3B"/>'
        '<polygon points="15,2.5 27,10 15,17.5 3,10" fill="#FFDF00"/>'
        '<circle cx="15" cy="10" r="4.3" fill="#002776"/>'),
}


def selo(local):
    """Bandeira do local quando temos uma; senão, um selo de traço na cor do texto."""
    if local in BANDEIRAS:
        return BANDEIRAS[local]
    return _BANDEIRA.format(
        '<rect x="1" y="1" width="28" height="18" rx="3" fill="none"'
        ' stroke="currentColor" stroke-width="1.2"/>'
        '<circle cx="15" cy="9" r="3.5" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        '<path d="M15 12.5 L15 16" stroke="currentColor" stroke-width="1.2"/>')
