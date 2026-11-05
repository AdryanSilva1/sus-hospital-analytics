import json
from datetime import date

import pandas as pd

from pipeline.config import ARQ_CONTROLE, PASTA_PROCESSADOS, TABELAS


def _ler(arquivo):
    if arquivo.exists():
        return pd.read_parquet(arquivo)
    return pd.DataFrame()


def _salvar(df, arquivo):
    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    df.to_parquet(arquivo, index=False)


def meses_salvos():
    """{(uf, ano): quantos meses já estão no resumo}"""
    controle = _ler(ARQ_CONTROLE)
    if controle.empty:
        return {}
    return {(r.uf, r.ano): r.meses for r in controle.itertuples()}


def salvar_ano(resumos, uf, ano, meses, ultimo_mes):
    """Troca o ano inteiro de um estado pelos resumos novos."""
    for nome, novo in resumos.items():
        atual = _ler(TABELAS[nome])
        if not atual.empty:
            atual = atual[~((atual["uf"] == uf) & (atual["ano"] == ano))]

        final = pd.concat([atual, novo], ignore_index=True)
        _salvar(final.sort_values(["uf", "ano"]).reset_index(drop=True), TABELAS[nome])

    controle = _ler(ARQ_CONTROLE)
    if not controle.empty:
        controle = controle[~((controle["uf"] == uf) & (controle["ano"] == ano))]

    linha = pd.DataFrame([{
        "uf": uf, "ano": ano, "meses": meses,
        "ultimo_mes": ultimo_mes, "atualizado_em": date.today().isoformat(),
    }])
    _salvar(pd.concat([controle, linha], ignore_index=True), ARQ_CONTROLE)


def salvar_tabela(df, arquivo):
    _salvar(df, arquivo)


def salvar_json(dados, arquivo):
    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
