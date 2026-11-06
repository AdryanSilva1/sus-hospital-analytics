"""Geometria dos mapas: centros, divisas e o polígono de cada estado."""

import numpy as np
import pytest

from dashboard.malha import _area_com_sinal, preparar_malha


def test_preparar_malha_aceita_multipolygon():
    ilha = [[[-48.5, -27.6], [-48.4, -27.6], [-48.4, -27.5], [-48.5, -27.6]]]
    continente = [[[-48.7, -27.7], [-48.6, -27.7], [-48.6, -27.5], [-48.65, -27.4], [-48.7, -27.7]]]
    geojson = {"features": [{
        "id": "420540", "properties": {"uf": "SC"},
        "geometry": {"type": "MultiPolygon", "coordinates": [ilha, continente]},
    }]}

    malha = preparar_malha(geojson)
    centro = malha["centros"].iloc[0]

    assert centro["lon"] == pytest.approx(-48.65)  # centro do pedaço maior
    assert np.isnan(malha["contornos"]["SC"][0]).sum() == 2  # um separador por pedaço


def _quadrado(x, y, uf, codigo):
    anel = [[x, y], [x, y + 1], [x + 1, y + 1], [x + 1, y], [x, y]]
    return {"id": codigo, "properties": {"uf": uf},
            "geometry": {"type": "Polygon", "coordinates": [anel]}}


def test_estado_junta_os_municipios_e_tira_a_divisa_de_dentro():
    # Dois quadrados lado a lado no mesmo estado viram um retângulo só
    malha = preparar_malha({"features": [_quadrado(0, 0, "SC", "1"), _quadrado(1, 0, "SC", "2")]})
    (estado,) = malha["estados"]["features"]
    (poligono,) = estado["geometry"]["coordinates"]
    (borda,) = poligono
    assert estado["id"] == "SC"
    assert len(borda) == 7  # 6 pontos da borda de fora + o ponto que fecha o anel
    assert {tuple(p) for p in borda} == {(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1)}


def test_estado_cercado_vira_buraco():
    # Um 3x3 em que o quadrado do meio é de outro estado (como o DF dentro de Goiás)
    quadrados = [_quadrado(x, y, "GO", f"{x}{y}") for x in range(3) for y in range(3) if (x, y) != (1, 1)]
    malha = preparar_malha({"features": [*quadrados, _quadrado(1, 1, "DF", "11")]})
    goias = next(e for e in malha["estados"]["features"] if e["id"] == "GO")
    (poligono,) = goias["geometry"]["coordinates"]
    assert len(poligono) == 2  # borda de fora + buraco


def test_preparar_malha_deixa_a_borda_no_sentido_horario():
    anti_horario = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    geojson = {"features": [{"id": "1", "properties": {"uf": "SC"},
                             "geometry": {"type": "Polygon", "coordinates": [anti_horario]}}]}

    borda = preparar_malha(geojson)["geojson"]["features"][0]["geometry"]["coordinates"][0][0]

    assert _area_com_sinal(borda) < 0
