# SUS Sul Analytics
### Internações hospitalares do SUS no Paraná, Santa Catarina e Rio Grande do Sul

Pipeline de dados + dashboard com **dados oficiais do DATASUS**.
O pipeline busca os arquivos direto do FTP do Ministério da Saúde, limpa, resume e
salva. O dashboard só lê o resultado. Todo mês o GitHub Actions roda tudo de novo
e os dados se atualizam sozinhos.

> Versão 2.0. A primeira versão usava um CSV exportado do TabNet, só de Santa Catarina.

---

## Como funciona

```
DATASUS (FTP oficial)          IBGE (API oficial)
        │                              │
        ▼                              ▼
  pipeline/extract.py  ── baixa os arquivos RD do SIH e os nomes dos municípios
        │
        ▼
  pipeline/transform.py ── limpa, traduz códigos (CID, procedimento, idade)
        │
        ▼
  pipeline/load.py ── salva tabelas resumidas em Parquet (data/processados)
        │
        ▼
  app.py (Streamlit) ── lê o Parquet e mostra
```

`.github/workflows/atualizar-dados.yml` roda o pipeline todo dia 15 e faz commit
dos dados novos.

---

## O que o painel mostra

Uma página só, no estilo de um painel Power BI:

- **Topo** — estado (Sul, PR, SC, RS), ano, o número da medida escolhida e a data da última atualização
- **Sistemas do corpo** — botões (Circulatório, Respiratório, Neoplasias...) que filtram o painel inteiro
- **Por estado e por município** — barras coloridas pelo estado
- **Mapa** — uma bolha por município, do tamanho da medida
- **Por diagnóstico (CID-10)** — tabela com barra de dados
- **Filtros** — faixa etária, raça/cor, sexo e tipo de procedimento (cirúrgico ou clínico)
- **Medidas** — internações, dias, dias por internação, óbitos, % de óbitos, valor AIH e valor médio
- **Por sistema** — tabela com todos os sistemas e total

---

## Tecnologias

- **Python** — pipeline e dashboard
- **Pandas** — limpeza e agregação
- **pyreaddbc + dbfread** — leitura dos arquivos `.dbc` do DATASUS
- **Parquet** — armazenamento leve das tabelas resumidas
- **Streamlit + Plotly** — dashboard
- **GitHub Actions** — atualização automática mensal
- **pytest** — testes das regras de transformação

---

## Como rodar

```bash
git clone https://github.com/AdryanSilva1/sus-hospital-analytics.git
cd sus-hospital-analytics

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-pipeline.txt
```

**1. Buscar os dados** (a primeira carga demora, são muitos arquivos)

```bash
python -m pipeline.run --uf SC --ano-inicial 2025   # teste rápido
python -m pipeline.run                              # tudo: PR, SC e RS desde 2019
```

**2. Abrir o dashboard**

```bash
python -m streamlit run app.py
```

Acesse **http://localhost:8501**

**Testes**

```bash
pytest -q
```

---

## Estrutura

```
sus-hospital-analytics/
├── app.py                     ← dashboard (monta a página)
├── pipeline/
│   ├── config.py              ← estados, ano inicial, endereços das fontes
│   ├── extract.py             ← FTP do DATASUS, CID-10, IBGE
│   ├── transform.py           ← limpeza e regras de negócio
│   ├── load.py                ← salva em Parquet, um ano por vez
│   └── run.py                 ← executa tudo em ordem
├── dashboard/
│   ├── dados.py               ← leitura, filtros, medidas e formatação (R$, %)
│   ├── visuais.py             ← barras, mapa e tabelas
│   ├── layout.py              ← blocos e logo
│   └── styles.css
├── tests/
│   └── test_transform.py
├── data/
│   ├── brutos/                ← .dbc baixados (fora do Git)
│   └── processados/           ← Parquet usado pelo dashboard
└── .github/workflows/
    └── atualizar-dados.yml
```

O pipeline gera três tabelas resumidas por ano: `por_municipio` (mapa e
barras), `por_cid` (tabela de diagnósticos) e `por_perfil` (faixa etária,
raça/cor e sexo). Quando sai um mês novo, o ano daquele mês é refeito inteiro.

---

## Regras de contagem

| Indicador | Como é calculado |
|---|---|
| Internação | AIH principal aprovada (`IDENT = 1`). AIHs de continuação ficam de fora para não contar duas vezes |
| Cirurgia | Procedimento principal do grupo 04 da tabela SIGTAP |
| Óbito hospitalar | `MORTE = 1` (morreu durante a internação) |
| Valor pago | `VAL_TOT` da AIH, valor nominal sem correção pela inflação |
| Município | Local do hospital (`MUNIC_MOV`), não onde o paciente mora |

## Limitações

- **Fila de espera e mortes na fila** não existem em base pública nacional, por isso não estão no painel.
- O DATASUS publica com alguns meses de atraso e pode corrigir meses recentes. Quando sai um mês novo, o pipeline refaz o ano inteiro daquele mês.
- Faixa etária, raça/cor e sexo filtram o número do topo e a tabela por sistema (as outras tabelas ficariam grandes demais com todos esses cortes).
- Em medidas de média e porcentagem, municípios e diagnósticos com menos de 50 internações ficam fora dos rankings.
- Só entram internações pagas pelo SUS.

---

## Fontes

- [SIH/SUS — DATASUS](https://datasus.saude.gov.br/) · FTP `ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados`
- [API de Localidades e de Malhas — IBGE](https://servicodados.ibge.gov.br/api/docs)
- [Tabela CID-10 — DATASUS](http://www2.datasus.gov.br/cid10/V2008/cid10.htm)
- Coordenadas dos municípios: [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros) (base aberta a partir do IBGE)
- [Tabela SIGTAP](http://sigtap.datasus.gov.br/)

---

## Autor

**Adryan Silva Santos**
Analista de Dados & Automação · Saúde

🔗 [LinkedIn](https://www.linkedin.com/in/adryan-silva-santos)
🔗 [GitHub](https://github.com/AdryanSilva1)
