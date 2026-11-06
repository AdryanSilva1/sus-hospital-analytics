import json
from datetime import date

import pandas as pd

from pipeline.config import PASTA_PROCESSADOS, TABELAS, arquivo_da_tabela


def _ler(arquivo):
    if arquivo.exists():
        return pd.read_parquet(arquivo)
    return pd.DataFrame()


def _salvar(df, arquivo):
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(arquivo, index=False)


def _sem_o_ano(df, ano):
    return df if df.empty else df[df["ano"] != ano]


def meses_salvos(uf):
    """{ano: quantos meses já estão no resumo} de um estado.

    Se faltar alguma tabela do estado (ex.: uma tabela nova no projeto),
    devolve vazio para o estado ser refeito inteiro.
    """
    if not all(arquivo_da_tabela(nome, uf).exists() for nome in TABELAS):
        return {}
    controle = _ler(arquivo_da_tabela("controle", uf))
    return {r.ano: r.meses for r in controle.itertuples()}


def salvar_ano(resumos, uf, ano, meses, ultimo_mes):
    """Troca o ano inteiro de um estado pelos resumos novos."""
    for nome, novo in resumos.items():
        arquivo = arquivo_da_tabela(nome, uf)
        final = pd.concat([_sem_o_ano(_ler(arquivo), ano), novo], ignore_index=True)
        _salvar(final.sort_values("ano").reset_index(drop=True), arquivo)

    arquivo = arquivo_da_tabela("controle", uf)
    linha = pd.DataFrame([{
        "uf": uf, "ano": ano, "meses": meses,
        "ultimo_mes": ultimo_mes, "atualizado_em": date.today().isoformat(),
    }])
    _salvar(pd.concat([_sem_o_ano(_ler(arquivo), ano), linha], ignore_index=True), arquivo)




def salvar_tabela(df, arquivo):
    _salvar(df, arquivo)


def salvar_json(dados, arquivo):
    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
