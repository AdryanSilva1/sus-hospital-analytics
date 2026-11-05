"""Onde o paciente mora × onde ele foi internado."""

import streamlit as st

from dashboard import visuais
from dashboard.componentes import aviso, cartao, grafico, tabela, tile, titulo
from dashboard.medidas import decimal, numero, por_100_mil, porcentagem

UF_DO_CODIGO = {"41": "PR", "42": "SC", "43": "RS"}
TAXA = "Internações por 100 mil hab."
MINIMO_HABITANTES = 5_000  # cidade muito pequena faz a taxa oscilar demais


def _parte(parte, todo):
    return porcentagem(parte / todo * 100) if todo else "—"


def numeros(fluxo, municipio):
    de_fora = fluxo["cod_residencia"] != fluxo["cod_municipio"]

    with st.container(horizontal=True, key="cartoes-fluxo"):
        if municipio is None:
            cartao("Internações de quem mora em outra cidade",
                   _parte(fluxo.loc[de_fora, "internacoes"].sum(), fluxo["internacoes"].sum()))
            outro_estado = fluxo["cod_residencia"].str[:2] != fluxo["cod_municipio"].str[:2]
            cartao("Internações de quem mora em outro estado",
                   _parte(fluxo.loc[outro_estado, "internacoes"].sum(), fluxo["internacoes"].sum()))
            return

        atendidos = fluxo[fluxo["cod_municipio"] == municipio]
        moradores = fluxo[fluxo["cod_residencia"] == municipio]
        cartao("Pacientes internados aqui", numero(atendidos["internacoes"].sum()))
        cartao("…que moram em outra cidade",
               _parte(atendidos.loc[de_fora, "internacoes"].sum(), atendidos["internacoes"].sum()))
        cartao("Moradores daqui internados em outra cidade",
               _parte(moradores.loc[de_fora, "internacoes"].sum(), moradores["internacoes"].sum()))


def taxa_por_residencia(painel):
    """Internações por 100 mil habitantes, contando pela cidade onde o paciente mora."""
    populacao = painel.tabelas["populacao"]
    if populacao is None:
        st.info("A população ainda não foi baixada. Rode `python -m pipeline.run` de novo.")
        return None

    # Conta todos os hospitais da região: morador de SC internado no PR também conta para SC
    fluxo = painel.dados("fluxo", ignorar=["uf", "cod_municipio"])
    df = (fluxo.groupby(["cod_residencia", "residencia"])
          [["internacoes", "obitos", "valor_total"]].sum().reset_index()
          .rename(columns={"cod_residencia": "cod_municipio", "residencia": "municipio"}))
    df["uf"] = df["cod_municipio"].str[:2].map(UF_DO_CODIGO)
    df = df[df["uf"].isin(painel.ufs)].merge(populacao, on="cod_municipio")
    df = df[df["populacao"] >= MINIMO_HABITANTES]
    df["valor"] = por_100_mil(df["internacoes"], df["populacao"])
    return df.sort_values("valor", ascending=False)


def polos(fluxo):
    """Cidades que mais recebem pacientes de outras cidades."""
    de_fora = fluxo[fluxo["cod_residencia"] != fluxo["cod_municipio"]]
    df = de_fora.groupby(["cod_municipio", "municipio"])["internacoes"].sum().reset_index()
    df["uf"] = df["cod_municipio"].str[:2].map(UF_DO_CODIGO)
    return df.rename(columns={"internacoes": "valor"}).sort_values("valor", ascending=False).head(15)


def ligacoes(fluxo, municipio, de, para):
    """Top 10 cidades ligadas a `municipio` (de onde vêm ou para onde vão os pacientes)."""
    df = fluxo[(fluxo[de] == municipio) & (fluxo[para] != municipio)]
    nome = "residencia" if para == "cod_residencia" else "municipio"
    df = df.groupby([para, nome])["internacoes"].sum().reset_index()
    return df.rename(columns={"internacoes": "valor"}).sort_values("valor", ascending=False).head(10)


def mostrar(painel):
    municipio = st.session_state.cod_municipio
    fluxo = painel.dados("fluxo", ignorar=["cod_municipio"])
    st.caption("Esta aba conta internações (sem sistema do corpo e procedimento). "
               "Clique num município para ver de onde vêm os pacientes dele.")
    aviso(painel, "fluxo", nao_tem=["capitulo_cid", "tipo_procedimento"], tem=["cod_municipio"])
    numeros(fluxo, municipio)

    if municipio:
        esq, dir_ = st.columns(2)
        with esq, tile("fluxo-origem"):
            titulo("De onde vêm os pacientes internados aqui")
            df = ligacoes(fluxo, municipio, "cod_municipio", "cod_residencia")
            grafico(visuais.barras(df, "residencia", "Internações", "cod_residencia", clicavel=False))
        with dir_, tile("fluxo-destino"):
            titulo("Para onde vão os moradores daqui")
            df = ligacoes(painel.dados("fluxo", ignorar=["uf", "cod_municipio"]),
                          municipio, "cod_residencia", "cod_municipio")
            grafico(visuais.barras(df, "municipio", "Internações", "cod_municipio"),
                    "fluxo-destino", "cod_municipio")

    taxa = taxa_por_residencia(painel)
    esq, dir_ = st.columns([1.5, 1])
    with esq, tile("fluxo-mapa"):
        titulo(f"{TAXA} (pela cidade onde o paciente mora)",
               f"População do Censo 2022 (IBGE). Cidades com menos de "
               f"{numero(MINIMO_HABITANTES)} habitantes ficam de fora.")
        if taxa is not None and painel.tabelas["malha"] is not None:
            fig = visuais.mapa_pintado(taxa, TAXA, painel.tabelas["malha"], st.session_state.f_uf,
                                       municipio, formatador=decimal)
            grafico(fig, "fluxo-mapa", "cod_municipio", zoom=True)
    with dir_, tile("fluxo-polos"):
        titulo("Cidades que mais recebem pacientes de fora")
        grafico(visuais.barras(polos(fluxo), "municipio", "Internações", "cod_municipio",
                               municipio, cor="uf"), "fluxo-polos", "cod_municipio")

    if taxa is not None:
        with tile("fluxo-ranking"):
            titulo(f"Ranking: {TAXA}")
            taxa = taxa.assign(populacao=taxa["populacao"].map(numero))
            tabela(taxa, {"municipio": "Município", "uf": "UF", "populacao": "População"},
                   "fluxo-ranking", "cod_municipio", TAXA, altura=420)
