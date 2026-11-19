from datetime import date
from pathlib import Path
import time

import requests

URL_BASE = "https://siros.anac.gov.br/siros/registros/diversos/vra"
PASTA_BRONZE = Path("data/bronze")
ANO_INICIAL = 2020


def nomes_candidatos(ano: int, mes: int) -> list[str]:
    """Padrões de nome já vistos no SIROS, do mais recente ao mais antigo."""
    return [
        f"VRA_{ano}_{mes:02d}.csv",  # ex.: VRA_2026_09.csv
        f"VRA_{ano}{mes}.csv",       # ex.: VRA_20269.csv
        f"VRA_{ano}{mes:02d}.csv",   # ex.: VRA_202609.csv
        f"VRA_{ano}_{mes}.csv",      # ex.: VRA_2026_9.csv
    ]


def baixar_mes(ano: int, mes: int) -> None:
    """Baixa o VRA de um mês, se ainda não existir na bronze."""
    # Nome padronizado na bronze, independentemente do nome na fonte
    destino = PASTA_BRONZE / f"VRA_{ano}_{mes:02d}.csv"

    if destino.exists():
        print(f"[pulado]  {destino.name} já existe")
        return

    for nome in nomes_candidatos(ano, mes):
        url = f"{URL_BASE}/{ano}/{nome}"
        try:
            resposta = requests.get(url, timeout=120)
        except requests.RequestException as erro:
            print(f"[erro]    falha de conexão em {url}: {erro}")
            return

        if resposta.status_code == 200:
            temporario = destino.with_suffix(".part")
            temporario.write_bytes(resposta.content)
            temporario.rename(destino)
            tamanho_mb = destino.stat().st_size / 1_000_000
            print(f"[ok]      {nome} -> {destino.name} ({tamanho_mb:.1f} MB)")
            time.sleep(1)  # pausa para não sobrecarregar o servidor
            return

    print(f"[aviso]   {ano}-{mes:02d} não encontrado em nenhum padrão de nome")


if __name__ == "__main__":
    PASTA_BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today()

    for ano in range(ANO_INICIAL, hoje.year + 1):
        for mes in range(1, 13):
            # Não tenta meses que ainda não aconteceram
            if (ano, mes) > (hoje.year, hoje.month):
                break
            baixar_mes(ano, mes)