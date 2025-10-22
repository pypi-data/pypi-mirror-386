from datetime import datetime
import json
import os

import click
import pandas as pd

from mtcli.logger import setup_logger

log = setup_logger()


def formatar_numero(valor: float, decimais: int = 2) -> str:
    """Formata número no padrão brasileiro (1.234,56)."""
    try:
        return f"{valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)


def exibir_rvo(
    dados: dict,
    timeframe: str,
    tipo_volume: str,
    export: bool = False,
    json_out: bool = False,
):
    """Exibe o RVO formatado e exporta CSV/JSON."""
    symbol = dados["symbol"]
    rvo_atual = dados["rvo_atual"]
    vol_atual = dados["volume_atual"]
    vol_medio = dados["volume_medio"]
    historico = dados["historico"]

    direcao = "acima da média" if rvo_atual > 1 else "abaixo da média"
    cor_direcao = "green" if rvo_atual > 1 else "red"

    click.echo(click.style("Indicador de Volume Relativo (RVO)", fg="cyan", bold=True))
    click.echo(click.style(f"Ativo: {symbol}", fg="yellow"))
    click.echo(f"Timeframe: {timeframe}")
    click.echo(f"Tipo de volume: {tipo_volume}")
    click.echo(f"Volume atual: {formatar_numero(vol_atual, 0)}")
    click.echo(f"Volume médio: {formatar_numero(vol_medio, 0)}")
    click.echo(
        click.style(
            f"RVO atual: {formatar_numero(rvo_atual, 2)} — {direcao}", fg=cor_direcao
        )
    )

    click.echo("\nHistórico recente do RVO:")
    linhas = []
    rvo_anterior = None

    for item in historico:
        ts = datetime.fromtimestamp(item["time"])
        valor = item["rvo"]

        seta = ""
        delta = ""
        if rvo_anterior is not None:
            if valor > rvo_anterior:
                seta = click.style("↑", fg="green")
            elif valor < rvo_anterior:
                seta = click.style("↓", fg="red")
            else:
                seta = click.style("→", fg="yellow")

            try:
                variacao = ((valor - rvo_anterior) / rvo_anterior) * 100
                delta = f"{variacao:+.1f}%".replace(".", ",")
            except Exception:
                delta = "—"
        else:
            delta = "—"

        click.echo(f"  {ts:%d/%m %H:%M} — {formatar_numero(valor, 2)} {seta} ({delta})")
        linhas.append(
            {
                "datetime": ts.isoformat(),
                "rvo": round(valor, 4),
                "delta_%": delta,
            }
        )
        rvo_anterior = valor

    # cria pasta exports se necessário
    exports_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(exports_dir, exist_ok=True)

    # Exportar CSV
    if export:
        nome_arquivo = os.path.join(exports_dir, f"rvo_{symbol}_{timeframe}_{tipo_volume}.csv")
        df = pd.DataFrame(linhas)
        df.to_csv(nome_arquivo, index=False)
        click.echo(
            click.style(
                f"\nArquivo CSV exportado: {os.path.abspath(nome_arquivo)}", fg="cyan"
            )
        )
        log.info(f"Arquivo CSV exportado: {nome_arquivo}")

    # Exportar JSON
    if json_out:
        nome_arquivo = os.path.join(exports_dir, f"rvo_{symbol}_{timeframe}_{tipo_volume}.json")
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(linhas, f, ensure_ascii=False, indent=2)
        click.echo(
            click.style(
                f"Arquivo JSON exportado: {os.path.abspath(nome_arquivo)}", fg="cyan"
            )
        )
        log.info(f"Arquivo JSON exportado: {nome_arquivo}")
