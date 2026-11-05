"""O que todas as abas precisam saber: dados, filtros, medida e período."""

from dataclasses import dataclass

from dashboard.dados import filtros_fora, recorte, tabela_principal

NOMES_UF = {"Sul": "Região Sul", "PR": "Paraná", "SC": "Santa Catarina", "RS": "Rio Grande do Sul"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


@dataclass
class Painel:
    tabelas: dict
    filtros: dict      # coluna -> valor, ver filtros.atuais()
    medida: str        # medida escolhida no topo
    ano: int
    ultimo_mes: int    # último mês com dado no ano escolhido
    anos: list         # todos os anos disponíveis, do mais novo ao mais antigo

    @property
    def principal(self):
        return tabela_principal(self.filtros)

    @property
    def ufs(self):
        return self.filtros["uf"]

    @property
    def periodo(self):
        if self.ultimo_mes == 12:
            return str(self.ano)
        return f"{self.ano} · jan a {MESES[self.ultimo_mes - 1]}"

    def dados(self, nome=None, ignorar=(), **trocar):
        """Tabela `nome` (ou a principal) com os filtros atuais.

        `trocar` muda um filtro só nesta consulta, ex.: ano=2024.
        """
        filtros = {**self.filtros, **trocar}
        return recorte(self.tabelas, nome or self.principal, filtros, ignorar)

    def mesmo_periodo_do_ano_anterior(self):
        """(atual, anterior) da tabela por mês, com os mesmos meses nos dois anos.

        None quando não dá para comparar: a tabela por mês não tem região,
        município, CID nem perfil, e o primeiro ano não tem ano anterior.
        """
        if filtros_fora("mes", self.filtros) or self.ano - 1 not in self.anos:
            return None
        anterior = self.dados("mes", ano=self.ano - 1)
        return self.dados("mes"), anterior[anterior["mes"] <= self.ultimo_mes]
