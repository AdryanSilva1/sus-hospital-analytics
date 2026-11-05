"""Página principal, no estilo de um painel do Power BI."""

import streamlit as st

from dashboard import filtros, icones, visuais
from dashboard.componentes import aviso, grafico, html, tabela, tabela_pbi, tile, titulo
from dashboard.medidas import MEDIDAS, calcular, tirar_pequenos, total

# Altura das duas faixas de blocos (px)
ALTURA_FAIXA_1 = 450
ALTURA_FAIXA_2 = 440
ALTURA_MAPA = ALTURA_FAIXA_1 - 70

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


def cores_das_regioes(painel):
    """Cor de cada região, da que tem mais internações para a que tem menos."""
    por_regiao = calcular(painel.dados("municipio", ignorar=["regiao", "cod_municipio"]),
                          ["regiao"], "Internações")
    return visuais.cores_por(list(por_regiao["regiao"]))


def por_regiao(painel, cores):
    df = calcular(painel.dados("municipio", ignorar=["regiao", "cod_municipio"]),
                  ["regiao"], painel.medida)
    df = tirar_pequenos(df, painel.medida)
    fig = visuais.barras(df, "regiao", painel.medida, "regiao", st.session_state.regiao,
                         cor=("regiao", cores))
    grafico(fig, "painel-regiao", "regiao")


def por_municipio(painel, cores):
    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "regiao"], painel.medida)
    df = tirar_pequenos(df, painel.medida).head(60)
    fig = visuais.barras(df, "municipio", painel.medida, "cod_municipio",
                         st.session_state.cod_municipio, cor=("regiao", cores))
    grafico(fig, "painel-municipio", "cod_municipio")


def mapa(painel, cores):
    malha = painel.tabelas["malha"]
    if malha is None:
        st.info("O mapa ainda não foi baixado. Rode `python -m pipeline.run` de novo.")
        return

    df = calcular(painel.dados("municipio", ignorar=["cod_municipio"]),
                  ["cod_municipio", "municipio", "regiao", "uf"], painel.medida)
    fundo = st.segmented_control("Fundo", ["Ruas", "Simples"], default="Ruas", key="fundo_mapa",
                                 label_visibility="collapsed") or "Ruas"
    fig = visuais.mapa(tirar_pequenos(df, painel.medida), painel.medida, malha,
                       st.session_state.f_uf, st.session_state.cod_municipio,
                       com_ruas=fundo == "Ruas", cores=("regiao", cores), altura=ALTURA_MAPA)
    grafico(fig, "painel-mapa", "cod_municipio", zoom=True)


def por_doenca(painel):
    df = calcular(painel.dados("cid", ignorar=["cid"]), ["cid", "descricao", "capitulo_cid"],
                  painel.medida)
    df = tirar_pequenos(df, painel.medida)
    tabela(df, {"cid": "CID", "descricao": "Diagnóstico"}, "painel-cid", "cid",
           painel.medida, altura=ALTURA_FAIXA_2 - 80)
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
    """Duas faixas de blocos com a mesma altura, como num painel do Power BI."""
    cores = cores_das_regioes(painel)
    medida = painel.medida
    larguras = [1.2, 1.65, 1.6]

    regiao, centro, direita = st.columns(larguras)
    with regiao, tile("regiao", ALTURA_FAIXA_1):
        titulo(f"{medida} por região")
        por_regiao(painel, cores)
        aviso(painel, "municipio", tem=["regiao"])
    with centro, tile("mapa", ALTURA_FAIXA_1):
        titulo(f"{medida} por município no mapa")
        mapa(painel, cores)
    with direita:
        filtros_coluna, medidas_coluna = st.columns([1, 1.15])
        with filtros_coluna, tile("filtros", ALTURA_FAIXA_1):
            titulo("Filtros do paciente")
            filtros_do_paciente()
        with medidas_coluna, tile("medidas", ALTURA_FAIXA_1):
            titulo("Medida")
            lista_de_medidas()

    municipio, diagnostico, sistema = st.columns(larguras)
    with municipio, tile("municipio", ALTURA_FAIXA_2):
        titulo(f"{medida} por município")
        por_municipio(painel, cores)
    with diagnostico, tile("cid", ALTURA_FAIXA_2):
        titulo(f"{medida} por diagnóstico (CID-10)")
        por_doenca(painel)
    with sistema, tile("sistema", ALTURA_FAIXA_2):
        titulo(f"{medida} por sistema do corpo")
        por_sistema(painel)
