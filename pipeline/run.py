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


def _baixar_se_faltar(arquivo, descricao, baixar, salvar=load.salvar_tabela, refazer=False):
    """Baixa uma tabela de apoio que ainda não existe.

    Se falhar, só avisa: o resto do pipeline segue. A API do IBGE, por exemplo,
    não responde fora do Brasil (como nos servidores do GitHub Actions).
    """
    if arquivo.exists() and not refazer:
        return
    print(f"Baixando {descricao}...")
    try:
        salvar(baixar(), arquivo)
    except Exception as erro:
        print(f"  Aviso: não consegui baixar {descricao} ({erro})")


def baixar_tabelas_de_apoio():
    # A lista de municípios é refeita se for de uma versão antiga, ainda sem a região
    sem_regiao = ARQ_MUNICIPIOS.exists() and "regiao" not in pd.read_parquet(ARQ_MUNICIPIOS).columns

    _baixar_se_faltar(ARQ_MUNICIPIOS, "municípios e regiões (IBGE)",
                      lambda: extract.baixar_municipios(UFS), refazer=sem_regiao)
    _baixar_se_faltar(ARQ_CID10, "tabela CID-10 (DATASUS)", extract.baixar_cid10)
    _baixar_se_faltar(ARQ_MALHA, "contorno dos municípios (IBGE)",
                      lambda: extract.baixar_malha(UFS), salvar=load.salvar_json)
    _baixar_se_faltar(ARQ_POPULACAO, "população do Censo 2022 (IBGE)",
                      lambda: extract.baixar_populacao(UFS))


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
