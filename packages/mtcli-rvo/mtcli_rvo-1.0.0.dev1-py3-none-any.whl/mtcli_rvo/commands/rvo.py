import click

from mtcli.logger import setup_logger
from mtcli_rvo.conf import BARS, PERIOD, SYMBOL, VOLUME, HISTORICO
from mtcli_rvo.controllers.rvo_controller import processar_rvo
from mtcli_rvo.views.rvo_view import exibir_rvo

log = setup_logger()

@click.command(help="Plugin para cálculo e exibição do Volume Relativo (RVO).")
@click.version_option(package_name="mtcli-rvo")
@click.option(
    "--symbol",
    "-s",
    default=SYMBOL,
    show_default=True,
    help="Ticker do ativo a ser analisado.",
)
@click.option(
    "--period",
    "-p",
    "period",
    default=PERIOD,
    show_default=True,
    help="Timeframe a ser analisado (ex: M5, M15, H1).",
)
@click.option(
    "--bars",
    "-b",
    "bars",
    default=BARS,
    show_default=True,
    help="Número de barras para média do volume.",
)
@click.option(
    "--historico",
    "-h",
    default=HISTORICO,
    show_default=True,
    help="Número de candles a exibir no histórico.",
)
@click.option(
    "--volume",
    "-v",
    "volume",
    type=click.Choice(["tick", "real"]),
    default=VOLUME,
    show_default=True,
    help="Tipo de volume: 'tick' ou 'real'.",
)
@click.option(
    "--export", "-e", is_flag=True, help="Exporta o histórico do RVO para arquivo CSV."
)
@click.option(
    "--json", "-j", "json_out", is_flag=True, help="Exporta o histórico do RVO em formato JSON."
)
def rvo(symbol, period, bars, volume, historico, export, json_out):
    """
    Calcula e exibe o indicador RVO (Relative Volume Oscillator).
    """
    try:
        log.info(
            f"Calculando RVO para {symbol} ({period}, {bars} períodos, volume {volume}, histórico={historico}, export={export}, json={json_out})"
        )
        resultado = processar_rvo(
            symbol,
            timeframe=period,
            periodos=bars,
            historico=historico,
            tipo_volume=volume,
            export=export,
            json_out=json_out,
        )
        if resultado:
            exibir_rvo(resultado, timeframe=period, tipo_volume=volume, export=export, json_out=json_out)
        else:
            click.echo(click.style("Nenhum resultado retornado para o cálculo do RVO.", fg="red"))
    except Exception as e:
        log.exception("Erro ao executar comando rvo")
        click.echo(click.style(f"Erro: {e}", fg="red"))
