import pandas as pd

# Capítulos da CID-10 (faixa inicial, faixa final, nome curto)
CAPITULOS_CID = [
    ("A00", "B99", "Infecciosas"),
    ("C00", "D48", "Neoplasias"),
    ("D50", "D89", "Sangue"),
    ("E00", "E90", "Endócrinas"),
    ("F00", "F99", "Saúde Mental"),
    ("G00", "G99", "Sistema Nervoso"),
    ("H00", "H59", "Olhos"),
    ("H60", "H95", "Ouvido"),
    ("I00", "I99", "Circulatório"),
    ("J00", "J99", "Respiratório"),
    ("K00", "K93", "Digestivo"),
    ("L00", "L99", "Pele/Tecido"),
    ("M00", "M99", "Músculo/Osso"),
    ("N00", "N99", "Geniturinário"),
    ("O00", "O99", "Gravidez e Parto"),
    ("P00", "P96", "Perinatal"),
    ("Q00", "Q99", "Malformações"),
    ("R00", "R99", "Sintomas"),
    ("S00", "T98", "Lesões"),
    ("U00", "U99", "COVID e especiais"),
    ("V01", "Y98", "Causas Externas"),
    ("Z00", "Z99", "Outros Contatos"),
]

# Grupo do procedimento = 2 primeiros dígitos do código SIGTAP
GRUPOS_PROCEDIMENTO = {"03": "Clínico", "04": "Cirúrgico"}

SEXO = {"1": "Masculino", "2": "Feminino", "3": "Feminino"}

RACA = {"01": "Branca", "02": "Preta", "03": "Parda", "04": "Amarela", "05": "Indígena"}

FAIXAS_ETARIAS = [
    (0, 14, "0 a 14"),
    (15, 29, "15 a 29"),
    (30, 44, "30 a 44"),
    (45, 59, "45 a 59"),
    (60, 74, "60 a 74"),
    (75, 200, "75 ou mais"),
]

METRICAS = ["internacoes", "obitos", "valor_total", "dias_internado"]

# Colunas de cada tabela resumida (além de uf e ano)
AGRUPAMENTOS = {
    "municipio": ["cod_municipio", "capitulo_cid", "tipo_procedimento"],
    "perfil": ["capitulo_cid", "tipo_procedimento", "sexo", "faixa_etaria", "raca"],
    "cid": ["cid", "capitulo_cid", "tipo_procedimento"],
}


def capitulo_cid(cid):
    codigo = str(cid).strip().upper()[:3]

    for inicio, fim, nome in CAPITULOS_CID:
        if inicio <= codigo <= fim:
            return nome

    return "Não informado"


def tipo_procedimento(procedimento):
    grupo = str(procedimento).strip().zfill(10)[:2]
    return GRUPOS_PROCEDIMENTO.get(grupo, "Outros")


def idade_em_anos(cod_idade, idade):
    # COD_IDADE: 2 = dias, 3 = meses, 4 = anos, 5 = mais de 100 anos
    if cod_idade == "4":
        return idade
    if cod_idade == "5":
        return 100 + idade
    return 0


def faixa_etaria(anos):
    for inicio, fim, nome in FAIXAS_ETARIAS:
        if inicio <= anos <= fim:
            return nome
    return "Não informado"


def preparar(df):
    """Limpa o arquivo bruto do SIH e cria as colunas usadas no painel."""
    df = df.copy()

    # IDENT 1 = AIH principal. As de continuação (5) contariam a mesma
    # internação duas vezes.
    df = df[df["IDENT"].astype(str).str.strip() == "1"]

    for col in ["IDADE", "DIAS_PERM", "MORTE"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["internacoes"] = 1
    df["obitos"] = df["MORTE"]
    df["dias_internado"] = df["DIAS_PERM"]
    df["valor_total"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0.0)

    df["cod_municipio"] = df["MUNIC_MOV"].astype(str).str.strip().str[:6]
    df["cid"] = df["DIAG_PRINC"].astype(str).str.strip().str.upper().str[:3]
    df["capitulo_cid"] = df["cid"].map(capitulo_cid)
    df["tipo_procedimento"] = df["PROC_REA"].map(tipo_procedimento)
    df["sexo"] = df["SEXO"].astype(str).str.strip().map(SEXO).fillna("Ignorado")
    df["raca"] = df["RACA_COR"].astype(str).str.strip().str.zfill(2).map(RACA).fillna("Sem informação")

    anos = [idade_em_anos(str(c).strip(), i) for c, i in zip(df["COD_IDADE"], df["IDADE"])]
    df["faixa_etaria"] = [faixa_etaria(a) for a in anos]

    return df


def resumir(df, tabela):
    """Soma as métricas pelas colunas da tabela escolhida."""
    colunas = AGRUPAMENTOS[tabela]
    return df.groupby(colunas, observed=True)[METRICAS].sum().reset_index()


def juntar_meses(resumos, tabela, uf, ano):
    """Junta os resumos mensais de um ano num resumo anual."""
    colunas = AGRUPAMENTOS[tabela]
    anual = pd.concat(resumos).groupby(colunas, observed=True)[METRICAS].sum().reset_index()
    anual.insert(0, "ano", ano)
    anual.insert(0, "uf", uf)
    return anual
