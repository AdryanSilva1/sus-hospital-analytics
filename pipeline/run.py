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

from pipeline import extract, load, transform
from pipeline.config import ANO_INICIAL, ARQ_CID10, ARQ_CONTORNOS, ARQ_MUNICIPIOS, UFS


def processar_ano(uf, ano, arquivos):
    resumos = {nome: [] for nome in transform.AGRUPAMENTOS}
    total = 0

    for arquivo in arquivos:
        df = transform.preparar(extract.ler_dbc(extract.baixar_arquivo(arquivo)))
        total += len(df)

        for nome in resumos:
            resumos[nome].append(transform.resumir(df, nome))

    anuais = {nome: transform.juntar_meses(r, nome, uf, ano) for nome, r in resumos.items()}
    return anuais, total


def baixar_tabelas_de_apoio():
    if not ARQ_MUNICIPIOS.exists():
        print("Baixando municípios (IBGE)...")
        load.salvar_tabela(extract.baixar_municipios(UFS), ARQ_MUNICIPIOS)

    # As duas abaixo são opcionais: se falharem, o painel funciona sem elas
    if not ARQ_CID10.exists():
        print("Baixando tabela CID-10 (DATASUS)...")
        try:
            load.salvar_tabela(extract.baixar_cid10(), ARQ_CID10)
        except Exception as erro:
            print(f"  Aviso: não consegui baixar a CID-10 ({erro})")

    if not ARQ_CONTORNOS.exists():
        print("Baixando contorno dos estados (IBGE)...")
        try:
            load.salvar_tabela(extract.baixar_contornos(UFS), ARQ_CONTORNOS)
        except Exception as erro:
            print(f"  Aviso: não consegui baixar os contornos ({erro})")


def main():
    parser = argparse.ArgumentParser(description="Pipeline SUS Sul Analytics")
    parser.add_argument("--uf", choices=UFS, help="processa só um estado")
    parser.add_argument("--ano-inicial", type=int, default=ANO_INICIAL)
    args = parser.parse_args()

    ufs = [args.uf] if args.uf else UFS
    baixar_tabelas_de_apoio()

    print("Consultando arquivos no FTP do DATASUS...")
    disponiveis = extract.listar_arquivos_disponiveis()
    salvos = load.meses_salvos()

    for uf in ufs:
        for ano in range(args.ano_inicial, date.today().year + 1):
            meses = [m for m in range(1, 13) if extract.nome_arquivo(uf, ano, m) in disponiveis]

            # Ano sem arquivo ou sem mês novo: nada a fazer
            if not meses or salvos.get((uf, ano)) == len(meses):
                continue

            arquivos = [disponiveis[extract.nome_arquivo(uf, ano, m)] for m in meses]
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
