import pandas as pd

from pipeline import transform


def arquivo_falso():
    # Imita algumas linhas de um arquivo RD do SIH
    return pd.DataFrame({
        "ANO_CMPT":   ["2024"] * 4,
        "MES_CMPT":   ["03"] * 4,
        "IDENT":      ["1", "1", "1", "5"],
        "MUNIC_MOV":  ["420540", "420540", "420910", "420540"],
        "SEXO":       ["1", "3", "3", "1"],
        "RACA_COR":   ["01", "03", "99", "01"],
        "COD_IDADE":  ["4", "4", "3", "4"],
        "IDADE":      ["67", "34", "8", "67"],
        "DIAG_PRINC": ["I219", "O800", "J189", "I219"],
        "PROC_REA":   ["0406030014", "0310010039", "0303140151", "0406030014"],
        "DIAS_PERM":  ["5", "2", "4", "10"],
        "MORTE":      ["1", "0", "0", "0"],
        "VAL_TOT":    ["1500.50", "600.00", "350.25", "800.00"],
    })


def test_capitulo_cid():
    assert transform.capitulo_cid("I219") == "Circulatório"
    assert transform.capitulo_cid("C509") == "Neoplasias"
    assert transform.capitulo_cid("U071") == "COVID e especiais"
    assert transform.capitulo_cid("") == "Não informado"


def test_tipo_procedimento():
    assert transform.tipo_procedimento("0406030014") == "Cirúrgico"
    assert transform.tipo_procedimento("0303140151") == "Clínico"
    assert transform.tipo_procedimento("0801010010") == "Outros"


def test_faixa_etaria():
    assert transform.faixa_etaria(transform.idade_em_anos("4", 67)) == "60 a 74"
    assert transform.faixa_etaria(transform.idade_em_anos("3", 8)) == "0 a 14"
    assert transform.faixa_etaria(transform.idade_em_anos("5", 2)) == "75 ou mais"


def test_preparar():
    df = transform.preparar(arquivo_falso())

    assert len(df) == 3  # a AIH de continuação (IDENT 5) sai
    assert list(df["raca"]) == ["Branca", "Parda", "Sem informação"]
    assert list(df["cid"]) == ["I21", "O80", "J18"]


def test_juntar_meses_soma_os_meses():
    df = transform.preparar(arquivo_falso())
    marco = transform.resumir(df, "municipio")
    abril = transform.resumir(df, "municipio")

    anual = transform.juntar_meses([marco, abril], "municipio", "SC", 2024)
    florianopolis = anual[anual["cod_municipio"] == "420540"]

    assert florianopolis["internacoes"].sum() == 4
    assert florianopolis["obitos"].sum() == 2
    assert round(florianopolis["valor_total"].sum(), 2) == 4201.00
    assert set(anual["uf"]) == {"SC"} and set(anual["ano"]) == {2024}
