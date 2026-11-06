"""Página principal, no estilo de um painel do Power BI."""

from dataclasses import dataclass

import streamlit as st

from dashboard import filtros, icones, visuais
from dashboard.brasil import ESTADOS
from dashboard.componentes import aviso, grafico, html, tabela, tabela_pbi, tile, titulo
from dashboard.medidas import MEDIDAS, calcular, tirar_pequenos, total

# Altura dos blocos (px). Cada coluna soma a mesma altura, então todas
# terminam na mesma linha, como no Power BI.
ALTURA = {
    "regiao": 360, "municipio": 520,      # coluna da esquerda
    "mapa": 520, "cid": 360,              # coluna do meio
    "filtros": 330, "sistema": 550,       # coluna da direita
}
ALTURA_MAPA = ALTURA["mapa"] - 80

PERFIL = [
    ("faixa_etaria", "Faixa Etária", ["0 a 14", "15 a 29", "30 a 44", "45 a 59", "60 a 74", "75 ou mais"]),
    ("raca", "Raça/Cor", ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Sem informação"]),
    ("sexo", "Sexo", ["Feminino", "Masculino"]),
]


def _limpar_outros_focos(coluna):
    filtros.so_um_foco(coluna)
    st.session_state.versao += 1


def filtros_do_paciente():
    for coluna, rotulo, opcoes in PERFIL:
        st.selectbox(rotulo, ["Todos", *opcoes], key=coluna,
                     on_change=_limpar_outros_focos, args=(coluna,))
    st.selectbox("Procedimento", ["Todos", "Clínico", "Cirúrgico"], key="f_proc")


def lista_de_medidas():
    st.radio("Medida", list(MEDIDAS), key="w_medida", label_visibility="collapsed",
                 index=list(MEDIDAS).index(st.session_state.medida),
             format_func=lambda m: f"{icones.MEDIDAS[m]}  {m}",
             on_change=lambda: st.session_state.update(medida=st.session_state.w_medida))


@dataclass
class Grupo:
    """Como o primeiro gráfico agrupa: por estado (Brasil ou região do país) ou
    pelas regiões do IBGE (um estado só). O mapa e os municípios usam as mesmas cores."""
    coluna: str     # "uf" ou "regiao"
    rotulo: str     # "estado" ou "região"
    cores: dict     # valor da coluna -> cor


def agrupamento(painel):
    if len(painel.ufs) > 1:
        return Grupo("uf", "estado", visuais.CORES_UF)

    # Cor de cada região, da que tem mais internações para a que tem menos
    por_regiao = calcular(painel.dados("municipio", ignorar=["regiao", "cod_municipio"]),
                          ["regiao"], "Internações")
    return Grupo("regiao", "região", visuais.cores_por(list(por_regiao["regiao"])))


def por_grupo(painel, grupo):
    df = calcular(painel.dados("municipio", ignorar=["regiao", "cod_municipio"]),
                  [grupo.coluna], painel.medida)
    df = tirar_pequenos(df, painel.medida)
    if grupo.coluna == "uf":
        df["nome"] = df["uf"].map(ESTADOS)
        rotulo, escolhido = "nome", None
    else:
        rotulo, escolhido = "regiao", st.session_state.regiao

    fig = visuais.barras(df, rotulo, painel.medida, grupo.coluna, escolhido,
                         cor=(grupo.coluna, grupo.cores))
    grafico(fig, "painel-grupo", grupo.coluna)


def por_municipio(painel, grupo):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "uf", "regiao"], painel.medida)
    df = tirar_pequenos(df, painel.medida).head(60)
    if grupo.coluna == "uf":  # no país inteiro, o nome sozinho pode repetir
        df["municipio"] = df["municipio"] + " (" + df["uf"] + ")"
    fig = visuais.barras(df, "municipio", painel.medida, "cod_municipio",
                         st.session_state.cod_municipio, cor=(grupo.coluna, grupo.cores))
    grafico(fig, "painel-municipio", "cod_municipio")


def mapa(painel, grupo):
    texto, botoes = st.columns([2.6, 1], vertical_alignment="center")
    with texto:
        titulo(f"{painel.medida} por município no mapa")
    with botoes:
        # "Simples" abre em qualquer navegador; "Ruas" precisa de internet e WebGL
        fundo = st.segmented_control("Fundo", ["Simples", "Ruas"], default="Simples", key="fundo_mapa",
                                     label_visibility="collapsed") or "Simples"

    malha = painel.tabelas["malha"]
    if malha is None:
        st.info("O mapa ainda não foi baixado. Rode `python -m pipeline.run` de novo.")
        return

    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "regiao", "uf"], painel.medida)
    fig = visuais.mapa(tirar_pequenos(df, painel.medida), painel.medida, malha, painel.ufs,
                       st.session_state.cod_municipio, com_ruas=fundo == "Ruas",
                       cores=(grupo.coluna, grupo.cores), altura=ALTURA_MAPA)
    grafico(fig, "painel-mapa", "cod_municipio", zoom=True)


def por_doenca(painel):
    df = calcular(painel.dados("cid", ignorar=["cid"]), ["cid", "descricao", "capitulo_cid"],
                  painel.medida)
    df = tirar_pequenos(df, painel.medida)
    tabela(df, {"cid": "CID", "descricao": "Diagnóstico"}, "painel-cid", "cid",
           painel.medida, altura=ALTURA["cid"] - 70)
    aviso(painel, "cid")


def por_sistema(painel):
    base = painel.dados(ignorar=["capitulo_cid"])
    df = calcular(base, ["capitulo_cid"], painel.medida)
    linhas = [{"sistema": s, "icone": icones.sistema(s), "valor": v}
              for s, v in zip(df["capitulo_cid"], df["valor"])]
    escolhido = st.session_state.f_sistema if st.session_state.f_sistema != "Todos" else None
    html(tabela_pbi(
        linhas, [("icone", "", "ico"), ("sistema", "Sistema", "nome")], painel.medida,
        destaque=escolhido, total=total(base, painel.medida)))


def mostrar(painel):
    grupo = agrupamento(painel)
    medida = painel.medida
    esquerda, centro, direita = st.columns([1.15, 1.75, 1.6])

    with esquerda:
        with tile("regiao", ALTURA["regiao"]):
            titulo(f"{medida} por {grupo.rotulo}")
            por_grupo(painel, grupo)
            aviso(painel, "municipio", tem=["regiao"])
        with tile("municipio", ALTURA["municipio"]):
            titulo(f"{medida} por município")
            por_municipio(painel, grupo)

    with centro:
        with tile("mapa", ALTURA["mapa"]):
            mapa(painel, grupo)
        with tile("cid", ALTURA["cid"]):
            titulo(f"{medida} por diagnóstico (CID-10)")
            por_doenca(painel)

    with direita:
        filtros_coluna, medidas_coluna = st.columns([1, 1.15])
        with filtros_coluna, tile("filtros", ALTURA["filtros"]):
            filtros_do_paciente()
        with medidas_coluna, tile("medidas", ALTURA["filtros"]):
            lista_de_medidas()
        with tile("sistema", ALTURA["sistema"]):
            titulo(f"{medida} por sistema do corpo")
            por_sistema(painel)
