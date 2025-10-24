from mtcli_market.models.profile_model import calcular_profile


def obter_profile(
    symbol: str,
    bars: int,
    block: float,
    by: str,
    ib_minutes: int = 30,
    va_percent: float = 0.7,
    timeframe: str = "M1",
):
    resultado = calcular_profile(
        symbol=symbol,
        bars=bars,
        block=block,
        by=by,
        ib_minutes=ib_minutes,
        va_percent=va_percent,
        timeframe=timeframe,
    )
    return resultado
