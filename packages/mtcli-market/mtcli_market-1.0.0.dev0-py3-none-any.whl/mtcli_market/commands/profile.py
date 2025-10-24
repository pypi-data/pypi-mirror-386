import click

from mtcli_market.conf import (
    BARS,
    BLOCK,
    BY,
    SYMBOL,
)
from mtcli_market.controllers.profile_controller import obter_profile
from mtcli_market.views.profile_view import exibir_profile


@click.command()
@click.version_option(package_name="mtcli-market")
@click.option(
    "--symbol", "-s", default=SYMBOL, show_default=True, help="Ticker do ativo"
)
@click.option(
    "--bars",
    "-b",
    default=BARS,
    show_default=True,
    type=int,
    help="Número de candles ou ticks a usar",
)
@click.option(
    "--block",
    "-k",
    default=BLOCK,
    show_default=True,
    type=float,
    help="Tamanho de bloco de preço (em pontos)",
)
@click.option(
    "--by",
    type=click.Choice(["time", "ticks", "volume"]),
    default=BY,
    show_default=True,
    help="Base para o profile: time, ticks ou volume",
)
@click.option(
    "--ib-minutes",
    default=30,
    show_default=True,
    type=int,
    help="Duração (em minutos) do Initial Balance (IB)",
)
@click.option(
    "--va-percent",
    default=0.7,
    show_default=True,
    type=float,
    help="Percentual para cálculo da Value Area (ex: 0.7 = 70% do volume)",
)
@click.option(
    "--timeframe",
    default="M1",
    show_default=True,
    help=(
        "Timeframe para o cálculo do profile. Pode ser M1, M5, H1, D1, ou valores customizados como 2m (2 minutos), 3h (3 horas) ou 2d (2 dias)."
    ),
)
@click.option(
    "--compact/--verbose",
    default=True,
    show_default=True,
    help="Modo compacto (menos texto) ou verboso (texto descritivo). Compact é pensado para leitura programática.",
)
def profile(symbol, bars, block, by, ib_minutes, va_percent, timeframe, compact):
    """Calcula e exibe o Market Profile de um ativo, com saída textual acessível.

    Observações de acessibilidade: a saída é textual, sem caracteres gráficos. Ideal para leitores de tela.
    """
    resultado = obter_profile(
        symbol=symbol,
        bars=bars,
        block=block,
        by=by,
        ib_minutes=ib_minutes,
        va_percent=va_percent,
        timeframe=timeframe,
    )
    exibir_profile(resultado, symbol=symbol, compact=compact)


if __name__ == "__main__":
    profile()
