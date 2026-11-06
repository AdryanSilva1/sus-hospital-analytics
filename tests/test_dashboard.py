"""Regras do painel que não dependem de tela: medidas, recortes e filtros."""

from types import SimpleNamespace

import numpy as np
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


def test_preparar_malha_aceita_multipolygon():
    ilha = [[[-48.5, -27.6], [-48.4, -27.6], [-48.4, -27.5], [-48.5, -27.6]]]
    continente = [[[-48.7, -27.7], [-48.6, -27.7], [-48.6, -27.5], [-48.65, -27.4], [-48.7, -27.7]]]
    geojson = {"features": [{
        "id": "420540", "properties": {"uf": "SC"},
        "geometry": {"type": "MultiPolygon", "coordinates": [ilha, continente]},
    }]}

    malha = dados.preparar_malha(geojson)
    centro = malha["centros"].iloc[0]

    assert centro["lon"] == pytest.approx(-48.65)  # centro do pedaço maior
    assert np.isnan(malha["contornos"]["SC"][0]).sum() == 2  # um separador por pedaço


def _quadrado(x, y, uf, codigo):
    anel = [[x, y], [x, y + 1], [x + 1, y + 1], [x + 1, y], [x, y]]
    return {"id": codigo, "properties": {"uf": uf},
            "geometry": {"type": "Polygon", "coordinates": [anel]}}


def test_estado_junta_os_municipios_e_tira_a_divisa_de_dentro():
    # Dois quadrados lado a lado no mesmo estado viram um retângulo só
    malha = dados.preparar_malha({"features": [_quadrado(0, 0, "SC", "1"), _quadrado(1, 0, "SC", "2")]})
    (estado,) = malha["estados"]["features"]
    (poligono,) = estado["geometry"]["coordinates"]
    (borda,) = poligono
    assert estado["id"] == "SC"
    assert len(borda) == 7  # 6 pontos da borda de fora + o ponto que fecha o anel
    assert {tuple(p) for p in borda} == {(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1)}


def test_estado_cercado_vira_buraco():
    # Um 3x3 em que o quadrado do meio é de outro estado (como o DF dentro de Goiás)
    quadrados = [_quadrado(x, y, "GO", f"{x}{y}") for x in range(3) for y in range(3) if (x, y) != (1, 1)]
    malha = dados.preparar_malha({"features": [*quadrados, _quadrado(1, 1, "DF", "11")]})
    goias = next(e for e in malha["estados"]["features"] if e["id"] == "GO")
    (poligono,) = goias["geometry"]["coordinates"]
    assert len(poligono) == 2  # borda de fora + buraco


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


def test_preparar_malha_deixa_a_borda_no_sentido_horario():
    anti_horario = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    geojson = {"features": [{"id": "1", "properties": {"uf": "SC"},
                             "geometry": {"type": "Polygon", "coordinates": [anti_horario]}}]}

    borda = dados.preparar_malha(geojson)["geojson"]["features"][0]["geometry"]["coordinates"][0][0]

    assert dados._area_com_sinal(borda) < 0


def test_taxa_por_estado_soma_o_estado_inteiro():
    from dashboard.paginas.fluxo import taxa_por_estado

    moradores = pd.DataFrame({"uf": ["SC", "SC", "PR"], "internacoes": [10, 30, 5],
                              "populacao": [1_000, 3_000, 10_000]})
    df = taxa_por_estado(moradores).set_index("uf")["valor"]
    assert df["SC"] == pytest.approx(1_000)  # 40 internações / 4 mil hab.
    assert df["PR"] == pytest.approx(50)
