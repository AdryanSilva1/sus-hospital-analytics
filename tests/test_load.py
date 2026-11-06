"""A gravação por estado: cada estado no próprio arquivo, um ano trocado por vez."""

import pandas as pd

from pipeline import config, load


def resumo(uf, ano, internacoes):
    return pd.DataFrame({"uf": [uf], "ano": [ano], "internacoes": [internacoes]})


def test_cada_estado_fica_no_seu_arquivo_e_o_ano_e_trocado(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PASTA_PROCESSADOS", tmp_path)
    tabelas = {nome: None for nome in config.TABELAS if nome != "controle"}

    load.salvar_ano({n: resumo("SC", 2025, 10) for n in tabelas}, "SC", 2025, 3, 3)
    load.salvar_ano({n: resumo("PR", 2025, 20) for n in tabelas}, "PR", 2025, 3, 3)
    load.salvar_ano({n: resumo("SC", 2025, 15) for n in tabelas}, "SC", 2025, 4, 4)  # mês novo

    assert (tmp_path / "por_municipio" / "SC.parquet").exists()
    assert (tmp_path / "por_municipio" / "PR.parquet").exists()
    municipio = load.ler_tabela("municipio")
    assert municipio.set_index("uf")["internacoes"].to_dict() == {"PR": 20, "SC": 15}
    assert load.meses_salvos("SC") == {2025: 4}


def test_estado_com_tabela_faltando_e_refeito(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PASTA_PROCESSADOS", tmp_path)
    load.salvar_ano({"municipio": resumo("SC", 2025, 10)}, "SC", 2025, 3, 3)
    assert load.meses_salvos("SC") == {}
