"""
Roda o pipeline completo: extract -> transform -> load.

Uso:
    python -m pipeline.run                         # tudo que falta
    python -m pipeline.run --uf SC --ano-inicial 2025   # teste rápido

Os dados são resumidos por ano. Quando sai um mês novo no DATASUS,
o ano daquele mês é refeito inteiro (assim correções antigas também entram).
"""

import argparse
import ftplib
from datetime import date

import pandas as pd

from pipeline import extract, load, transform
from pipeline.config import ANO_INICIAL, ARQ_CID10, ARQ_MALHA, ARQ_MUNICIPIOS, ARQ_POPULACAO, TABELAS, UFS


def processar_ano(uf, ano, arquivos):
    """arquivos: {mês: nome do arquivo no FTP}"""
    resumos = {nome: [] for nome in transform.AGRUPAMENTOS}
    total = 0

    for mes, arquivo in arquivos.items():
        df = transform.preparar(extract.ler_dbc(extract.baixar_arquivo(arquivo)), mes)
        total += len(df)

        for nome in resumos:
            resumos[nome].append(transform.resumir(df, nome))

    anuais = {nome: transform.juntar_meses(r, nome, uf, ano) for nome, r in resumos.items()}
    return anuais, total


def baixar_tabelas_de_apoio():
    # Refaz a lista se ela for de uma versão antiga, ainda sem a região
    if not ARQ_MUNICIPIOS.exists() or "regiao" not in pd.read_parquet(ARQ_MUNICIPIOS).columns:
        print("Baixando municípios (IBGE)...")
        load.salvar_tabela(extract.baixar_municipios(UFS), ARQ_MUNICIPIOS)

    # As de baixo são opcionais: se falharem, o painel funciona sem elas
    if not ARQ_CID10.exists():
        print("Baixando tabela CID-10 (DATASUS)...")
        try:
            load.salvar_tabela(extract.baixar_cid10(), ARQ_CID10)
        except Exception as erro:
            print(f"  Aviso: não consegui baixar a CID-10 ({erro})")

    if not ARQ_MALHA.exists():
        print("Baixando contorno dos municípios (IBGE)...")
        try:
            load.salvar_json(extract.baixar_malha(UFS), ARQ_MALHA)
        except Exception as erro:
            print(f"  Aviso: não consegui baixar o mapa ({erro})")

    if not ARQ_POPULACAO.exists():
        print("Baixando população do Censo 2022 (IBGE)...")
        try:
            load.salvar_tabela(extract.baixar_populacao(UFS), ARQ_POPULACAO)
        except Exception as erro:
            print(f"  Aviso: não consegui baixar a população ({erro})")


def main():
    parser = argparse.ArgumentParser(description="Pipeline SUS Sul Analytics")
    parser.add_argument("--uf", choices=UFS, help="processa só um estado")
    parser.add_argument("--ano-inicial", type=int, default=ANO_INICIAL)
    args = parser.parse_args()

    ufs = [args.uf] if args.uf else UFS
    baixar_tabelas_de_apoio()

    print("Consultando arquivos no FTP do DATASUS...")
    disponiveis = extract.listar_arquivos_disponiveis()
    # Se faltar alguma tabela (ex.: uma tabela nova no projeto), refaz tudo.
    # Os .dbc já baixados ficam em data/brutos, então é rápido.
    salvos = load.meses_salvos() if all(a.exists() for a in TABELAS.values()) else {}

    for uf in ufs:
        for ano in range(args.ano_inicial, date.today().year + 1):
            meses = [m for m in range(1, 13) if extract.nome_arquivo(uf, ano, m) in disponiveis]

            # Ano sem arquivo ou sem mês novo: nada a fazer
            if not meses or salvos.get((uf, ano)) == len(meses):
                continue

            arquivos = {m: disponiveis[extract.nome_arquivo(uf, ano, m)] for m in meses}
            print(f"{uf} {ano}: {len(meses)} mês(es)...")

            try:
                resumos, total = processar_ano(uf, ano, arquivos)
                load.salvar_ano(resumos, uf, ano, len(meses), max(meses))
                print(f"  ok: {total:,} internações".replace(",", "."))
            except (*ftplib.all_errors, ValueError, KeyError) as erro:
                # Um ano com problema não derruba o resto
                print(f"  ERRO: {erro}")

    print("\nPronto.")


if __name__ == "__main__":
    main()
