"""Abre o painel de verdade (sem navegador) com dados falsos e confere cada aba."""

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import dados
from tests.dados_falsos import gerar

ABAS = ["📊 Visão geral", "💰 Gastos", "🗺️ Mapa e municípios", "🔁 Fluxo de pacientes",
        "🩺 Doenças (CID-10)", "👥 Perfil do paciente"]


@pytest.fixture
def painel(tmp_path, monkeypatch):
    gerar(tmp_path)
    monkeypatch.setattr(dados, "PASTA", tmp_path)
    dados.carregar.clear()
    return AppTest.from_file("../app.py", default_timeout=60)


@pytest.mark.parametrize("aba", ABAS)
def test_cada_aba_abre_sem_erro(painel, aba):
    painel.session_state["aba"] = aba
    painel.run()
    assert not painel.exception


def test_numeros_do_topo_aparecem(painel):
    painel.run()
    texto = " ".join(m.value for m in painel.markdown)
    assert "Internações" in texto and "R$" in texto
    assert "vs 2024" in texto  # comparação com o ano anterior


def test_filtrar_por_estado(painel):
    painel.run()
    painel.session_state["f_uf"] = "SC"
    painel.run()
    assert not painel.exception
    assert any("Estado: SC" in b.label for b in painel.button)


def test_sem_comparacao_quando_o_filtro_nao_existe_na_tabela_mensal(painel):
    painel.session_state["cod_municipio"] = "420001"
    painel.run()
    texto = " ".join(m.value for m in painel.markdown)
    assert "vs 2024" not in texto
