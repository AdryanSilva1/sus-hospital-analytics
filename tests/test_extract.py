"""Testa a leitura das respostas das APIs do IBGE sem acessar a internet."""

from pipeline import extract


class RespostaFalsa:
    def __init__(self, dados):
        self.dados = dados

    def raise_for_status(self):
        pass

    def json(self):
        return self.dados


def test_baixar_populacao(monkeypatch):
    resposta = [{"id": "93", "resultados": [{"series": [
        {"localidade": {"id": "4205407", "nome": "Florianópolis"}, "serie": {"2022": "537211"}},
        {"localidade": {"id": "4209102", "nome": "Joinville"}, "serie": {"2022": "616317"}},
    ]}]}]
    monkeypatch.setattr(extract.requests, "get", lambda *a, **k: RespostaFalsa(resposta))

    populacao = extract.baixar_populacao(["SC"])

    assert list(populacao["cod_municipio"]) == ["420540", "420910"]
    assert populacao["populacao"].sum() == 537211 + 616317


def test_baixar_malha_usa_codigo_de_6_digitos(monkeypatch):
    quadrado = [[[-48.6, -27.6], [-48.4, -27.6], [-48.4, -27.4], [-48.6, -27.6]]]
    resposta = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"codarea": "4205407"},
         "geometry": {"type": "Polygon", "coordinates": quadrado}},
    ]}
    monkeypatch.setattr(extract.requests, "get", lambda *a, **k: RespostaFalsa(resposta))

    malha = extract.baixar_malha(["SC"])

    municipio = malha["features"][0]
    assert municipio["id"] == "420540"
    assert municipio["properties"]["uf"] == "SC"


def test_baixar_municipios_traz_a_regiao(monkeypatch):
    resposta = [{"id": 4202404, "nome": "Blumenau",
                 "regiao-imediata": {"regiao-intermediaria": {"nome": "Blumenau"}}},
                {"id": 4200000, "nome": "Sem dados de região", "regiao-imediata": None}]
    monkeypatch.setattr(extract.requests, "get", lambda *a, **k: RespostaFalsa(resposta))

    municipios = extract.baixar_municipios(["SC"])

    assert list(municipios["regiao"]) == ["Blumenau", "Sem região"]
    assert municipios["cod_municipio"].iloc[0] == "420240"
