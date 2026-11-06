"""Regras do painel que não dependem de tela: medidas, recortes e filtros."""

from types import SimpleNamespace

import pandas as pd
import pytest

from dashboard import dados, filtros, medidas


def internacoes():
    return pd.DataFrame({
        "uf": ["SC", "SC", "PR"],
        "ano": [2025, 2025, 2025],
        "cod_municipio": ["420540", "420910", "410690"],
        "capitulo_cid": ["Circulatório", "Respiratório", "Circulatório"],
        "internacoes": [100, 50, 0],
        "obitos": [5, 1, 0],
        "valor_total": [200_000.0, 50_000.0, 0.0],
        "dias_internado": [500, 150, 0],
    })


# ── Medidas ──────────────────────────────────────────────────

def test_calcular_soma_e_divide_pela_medida():
    df = medidas.calcular(internacoes(), ["uf"], "Porcentagem de Óbitos")
    sc = df[df["uf"] == "SC"].iloc[0]
    assert sc["valor"] == pytest.approx(6 / 150 * 100)
    assert "PR" not in set(df["uf"])  # sem internação não dá para dividir


def test_total_sem_internacoes_nao_quebra():
    vazio = internacoes().iloc[2:]
    assert medidas.total(vazio, "Valor Médio AIH") == 0


@pytest.mark.parametrize("valor, esperado", [
    (1_234_567_890, "R$ 1,23 bi"), (45_600_000, "R$ 45,6 mi"), (1_894, "R$ 1.894"),
])
def test_reais(valor, esperado):
    assert medidas.reais(valor) == esperado


def test_decimal_usa_virgula_e_ponto_de_milhar():
    assert medidas.decimal(12345.67) == "12.345,7"


def test_variacao():
    assert medidas.variacao(110, 100) == "▲ 10,0%"
    assert medidas.variacao(90, 100) == "▼ 10,0%"
    assert medidas.variacao(10, 0) is None


# ── Recortes ─────────────────────────────────────────────────

def test_recorte_aplica_lista_e_ignora_o_pedido():
    tabelas = {"municipio": internacoes()}
    f = {"uf": ["SC"], "capitulo_cid": "Circulatório", "tipo_procedimento": "Todos"}

    assert len(dados.recorte(tabelas, "municipio", f)) == 1
    assert len(dados.recorte(tabelas, "municipio", f, ignorar=["capitulo_cid"])) == 2


def test_tabela_principal_segue_o_filtro_de_foco():
    assert dados.tabela_principal({"cid": None}) == "municipio"
    assert dados.tabela_principal({"cid": "I21"}) == "cid"
    assert dados.tabela_principal({"sexo": "Feminino"}) == "perfil"
    assert dados.filtros_fora("municipio", {"cid": "I21", "cod_municipio": None}) == ["cid"]


# ── Filtros (cliques) ────────────────────────────────────────

class Estado(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


@pytest.fixture
def sessao(monkeypatch):
    estado = Estado()
    monkeypatch.setattr(filtros, "st", SimpleNamespace(session_state=estado))
    filtros.iniciar()
    return estado


def test_clicar_de_novo_desmarca(sessao):
    filtros.definir("uf", "SC")
    assert sessao.f_uf == "SC"
    filtros.definir("uf", "SC")
    assert sessao.f_uf == "Brasil"


def test_municipio_e_cid_nao_ficam_juntos(sessao):
    filtros.definir("cid", "I21")
    filtros.definir("cod_municipio", "420540")
    assert sessao.cid is None and sessao.cod_municipio == "420540"


def test_cada_clique_troca_a_versao_dos_graficos(sessao):
    antes = sessao.versao
    filtros.definir("capitulo_cid", "Circulatório")
    assert sessao.versao == antes + 1


def test_taxa_por_estado_soma_o_estado_inteiro():
    from dashboard.paginas.fluxo import taxa_por_estado

    moradores = pd.DataFrame({"uf": ["SC", "SC", "PR"], "internacoes": [10, 30, 5],
                              "populacao": [1_000, 3_000, 10_000]})
    df = taxa_por_estado(moradores).set_index("uf")["valor"]
    assert df["SC"] == pytest.approx(1_000)  # 40 internações / 4 mil hab.
    assert df["PR"] == pytest.approx(50)
