"""Uma página do painel por arquivo. Cada uma tem a função mostrar(painel)."""

from dashboard.paginas import fluxo, gastos, principal

# caminho na URL: (título no menu, módulo)
PAGINAS = {
    "painel": ("Painel", principal),
    "gastos": ("Gastos e evolução", gastos),
    "fluxo": ("Fluxo de pacientes", fluxo),
}
