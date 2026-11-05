"""Abre o painel de verdade (sem navegador) com dados falsos e confere cada página."""

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import dados
from dashboard.paginas import PAGINAS
from tests.dados_falsos import gerar


@pytest.fixture
def pasta_falsa(tmp_path, monkeypatch):
    gerar(tmp_path)
    monkeypatch.setattr(dados, "PASTA", tmp_path)
    dados.carregar.clear()


def abrir(pagina="painel", **estado):
    teste = AppTest.from_file("abrir_pagina.py", default_timeout=60)
    teste.session_state["pagina"] = pagina
    for chave, valor in estado.items():
        teste.session_state[chave] = valor
    return teste.run()


def texto(teste):
    return " ".join(m.value for m in teste.markdown)


def test_app_abre_sem_erro(pasta_falsa):
    assert not AppTest.from_file("../app.py", default_timeout=60).run().exception


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_abre_sem_erro(pasta_falsa, pagina):
    assert not abrir(pagina).exception


@pytest.mark.parametrize("medida", ["Óbitos", "Porcentagem de Óbitos", "Valor Médio AIH"])
def test_trocar_a_medida(pasta_falsa, medida):
    teste = abrir(medida=medida)
    assert not teste.exception
    assert medida in texto(teste)


def test_numero_principal_compara_com_o_ano_anterior(pasta_falsa):
    assert "vs 2024" in texto(abrir())


def test_sem_comparacao_quando_o_filtro_nao_existe_na_tabela_mensal(pasta_falsa):
    assert "vs 2024" not in texto(abrir(cod_municipio="420001"))


def test_filtro_aparece_como_etiqueta(pasta_falsa):
    teste = abrir(f_uf="SC", f_sistema="Circulatório", sexo="Feminino")
    assert not teste.exception
    etiquetas = [b.label for b in teste.button]
    assert any("Estado: SC" in e for e in etiquetas)
    assert any("Sexo: Feminino" in e for e in etiquetas)


def test_funciona_sem_os_dados_do_ibge(pasta_falsa, tmp_path):
    for arquivo in ["municipios.parquet", "municipios.geojson", "populacao.parquet"]:
        (tmp_path / arquivo).unlink()
    for pagina in PAGINAS:
        assert not abrir(pagina).exception
