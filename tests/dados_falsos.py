"""Gera uma pasta data/processados FALSA, pequena, para testar o painel sem o DATASUS.

Uso manual:  python -m tests.dados_falsos data/processados
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.transform import CAPITULOS_CID, FAIXAS_ETARIAS

ESTADOS = {"PR": ("41", -24.7, -51.5), "SC": ("42", -27.3, -50.5), "RS": ("43", -29.8, -53.0)}
SISTEMAS = [nome for _, _, nome in CAPITULOS_CID][:8]
CIDS = [("I21", "Circulatório"), ("J18", "Respiratório"), ("O80", "Gravidez e Parto"),
        ("C50", "Neoplasias"), ("K80", "Digestivo")]
PROCEDIMENTOS = ["Clínico", "Cirúrgico"]
ANOS = [2024, 2025]


def _metricas(rng, n):
    internacoes = rng.integers(60, 400, n)
    return {
        "internacoes": internacoes,
        "obitos": (internacoes * rng.uniform(0.01, 0.08, n)).astype(int),
        "valor_total": internacoes * rng.uniform(800, 3000, n),
        "dias_internado": internacoes * rng.integers(2, 8, n),
    }


def _tabela(rng, colunas, valores, uf, ano):
    df = pd.MultiIndex.from_product(valores, names=colunas).to_frame(index=False)
    df = df.assign(**_metricas(rng, len(df)))
    df.insert(0, "ano", ano)
    df.insert(0, "uf", uf)
    return df


def _salvar_por_estado(df, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    for uf, parte in df.groupby("uf"):
        parte.to_parquet(pasta / f"{uf}.parquet", index=False)


def gerar(pasta, municipios_por_estado=12):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)

    municipios, malha = [], []
    for uf, (prefixo, lat, lon) in ESTADOS.items():
        lado = int(municipios_por_estado ** 0.5) + 1
        for i in range(municipios_por_estado):
            codigo = f"{prefixo}{i:04d}"
            # Municípios falsos em grade, um encostado no outro
            x, y = lon + (i % lado - lado / 2) * 0.4, lat + (i // lado - lado / 2) * 0.4
            municipios.append({"cod_municipio": codigo, "municipio": f"Cidade {uf} {i}", "uf": uf,
                               "regiao": f"Região {uf} {i % 5 + 1}"})
            borda = [[x - .2, y - .2], [x + .2, y - .2], [x + .2, y + .2], [x - .2, y + .2], [x - .2, y - .2]]
            malha.append({"type": "Feature", "id": codigo, "properties": {"uf": uf},
                          "geometry": {"type": "Polygon", "coordinates": [borda]}})
    municipios = pd.DataFrame(municipios)
    codigos = list(municipios["cod_municipio"])

    tabelas = {nome: [] for nome in ["municipio", "perfil", "cid", "mes", "fluxo"]}
    for ano in ANOS:
        for uf in ESTADOS:
            do_estado = list(municipios.loc[municipios["uf"] == uf, "cod_municipio"])
            tabelas["municipio"].append(_tabela(
                rng, ["cod_municipio", "capitulo_cid", "tipo_procedimento"],
                [do_estado, SISTEMAS, PROCEDIMENTOS], uf, ano))
            tabelas["perfil"].append(_tabela(
                rng, ["capitulo_cid", "tipo_procedimento", "sexo", "faixa_etaria", "raca"],
                [SISTEMAS, PROCEDIMENTOS, ["Feminino", "Masculino"],
                 [f for _, _, f in FAIXAS_ETARIAS], ["Branca", "Parda", "Preta"]], uf, ano))
            cid = _tabela(rng, ["cid", "tipo_procedimento"], [[c for c, _ in CIDS], PROCEDIMENTOS], uf, ano)
            cid.insert(3, "capitulo_cid", cid["cid"].map(dict(CIDS)))
            tabelas["cid"].append(cid)
            meses = range(1, 13) if ano < ANOS[-1] else range(1, 9)
            tabelas["mes"].append(_tabela(
                rng, ["mes", "capitulo_cid", "tipo_procedimento"],
                [list(meses), SISTEMAS, PROCEDIMENTOS], uf, ano))
            tabelas["fluxo"].append(_tabela(
                rng, ["cod_residencia", "cod_municipio"], [codigos[::3] + do_estado, do_estado], uf, ano))

    for nome, partes in tabelas.items():
        _salvar_por_estado(pd.concat(partes), pasta / f"por_{nome}")

    municipios.to_parquet(pasta / "municipios.parquet", index=False)
    pd.DataFrame({"cod_municipio": codigos, "populacao": rng.integers(8_000, 600_000, len(codigos))}
                 ).to_parquet(pasta / "populacao.parquet", index=False)
    pd.DataFrame({"cid": [c for c, _ in CIDS], "descricao": [f"Doença {c}" for c, _ in CIDS]}
                 ).to_parquet(pasta / "cid10.parquet", index=False)
    (pasta / "municipios.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": malha}))
    _salvar_por_estado(pd.DataFrame([{"uf": uf, "ano": ano, "meses": 12 if ano < ANOS[-1] else 8,
                                      "ultimo_mes": 12 if ano < ANOS[-1] else 8,
                                      "atualizado_em": "2026-11-05"}
                                     for uf in ESTADOS for ano in ANOS]), pasta / "controle")


if __name__ == "__main__":
    gerar(sys.argv[1] if len(sys.argv) > 1 else "data/processados", municipios_por_estado=60)
