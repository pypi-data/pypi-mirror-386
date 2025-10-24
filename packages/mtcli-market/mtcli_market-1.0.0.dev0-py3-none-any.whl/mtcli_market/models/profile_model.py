from collections import OrderedDict, defaultdict
from math import floor
from typing import Any

import MetaTrader5 as mt5

from mtcli.logger import setup_logger
from mtcli.mt5_context import mt5_conexao

log = setup_logger()


def _mapear_timeframe(timeframe: str | int) -> int:
    mapping = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    if isinstance(timeframe, int):
        minutos = timeframe
    else:
        tf_str = str(timeframe).upper().strip()
        if tf_str in mapping:
            return mapping[tf_str]
        minutos = 1
        if tf_str.endswith("M"):
            minutos = int(tf_str[:-1] or 1)
        elif tf_str.endswith("H"):
            minutos = int(tf_str[:-1] or 1) * 60
        elif tf_str.endswith("D"):
            minutos = int(tf_str[:-1] or 1) * 1440

    if minutos <= 1:
        return mt5.TIMEFRAME_M1
    elif minutos <= 5:
        return mt5.TIMEFRAME_M5
    elif minutos <= 15:
        return mt5.TIMEFRAME_M15
    elif minutos <= 30:
        return mt5.TIMEFRAME_M30
    elif minutos <= 60:
        return mt5.TIMEFRAME_H1
    elif minutos <= 240:
        return mt5.TIMEFRAME_H4
    else:
        return mt5.TIMEFRAME_D1


def _range_blocks(low: float, high: float, block: float) -> list[float]:
    low_b = floor(low / block) * block
    high_b = floor(high / block) * block
    blocks = []
    b = high_b
    while b >= low_b:
        blocks.append(round(b, 8))
        b -= block
    return blocks


def _distribuir_volume_uniforme(
    volume: float, blocks: list[float]
) -> dict[float, float]:
    if not blocks:
        return {}
    per = volume / len(blocks)
    return {b: per for b in blocks}


def calcular_profile(
    symbol: str,
    bars: int,
    block: float,
    by: str = "time",
    ib_minutes: int = 30,
    va_percent: float = 0.7,
    timeframe: str | int = "M1",
) -> dict[str, Any]:
    tf = _mapear_timeframe(timeframe)
    with mt5_conexao():
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            log.warning("Nenhum dado retornado para %s", symbol)
            return {}

        profile = defaultdict(float)
        tpo = defaultdict(int)

        for r in rates:
            low = float(r["low"])
            high = float(r["high"])
            tick_vol = float(r["tick_volume"])
            real_vol = float(r["real_volume"])
            blocks = _range_blocks(low, high, block)

            if by == "time":
                for b in blocks:
                    tpo[b] += 1
                    profile[b] += 1
            elif by == "ticks":
                dist = _distribuir_volume_uniforme(tick_vol, blocks)
                for b, v in dist.items():
                    profile[b] += v
                    tpo[b] += 1
            elif by == "volume":
                vol = real_vol or tick_vol
                dist = _distribuir_volume_uniforme(vol, blocks)
                for b, v in dist.items():
                    profile[b] += v
                    tpo[b] += 1

        ordered_profile = OrderedDict(
            sorted(profile.items(), key=lambda x: x[0], reverse=True)
        )
        ordered_tpo = OrderedDict(sorted(tpo.items(), key=lambda x: x[0], reverse=True))

        total_volume = sum(ordered_profile.values())
        poc = (
            max(ordered_profile.items(), key=lambda x: x[1])[0]
            if ordered_profile
            else None
        )

        def calcular_value_area(
            profile_map: dict[float, float], percent: float
        ) -> tuple[float, float, list[float]]:
            if not profile_map or percent <= 0 or percent > 1:
                return (None, None, [])
            target = sum(profile_map.values()) * percent
            items = sorted(profile_map.items(), key=lambda x: x[1], reverse=True)
            acum, selected = 0, []
            for price, vol in items:
                selected.append((price, vol))
                acum += vol
                if acum >= target:
                    break
            prices = [p for p, _ in selected]
            return (max(prices), min(prices), prices)

        vah, val, va_prices = (None, None, [])
        if ordered_profile:
            vah, val, va_prices = calcular_value_area(dict(ordered_profile), va_percent)

        hvn, lvn = [], []
        if ordered_profile:
            vols = list(ordered_profile.values())
            media = sum(vols) / len(vols)
            desvio = (sum((v - media) ** 2 for v in vols) / len(vols)) ** 0.5
            for price, vol in ordered_profile.items():
                if vol >= media + desvio:
                    hvn.append(price)
                elif vol <= max(0.0, media - desvio):
                    lvn.append(price)

        start_time = rates[0]["time"]
        limite = start_time + ib_minutes * 60
        ib_rates = [r for r in rates if r["time"] <= limite]
        ib_high = max(r["high"] for r in ib_rates) if ib_rates else None
        ib_low = min(r["low"] for r in ib_rates) if ib_rates else None

        return {
            "profile": ordered_profile,
            "tpo": ordered_tpo,
            "total_volume": total_volume,
            "poc": poc,
            "vah": vah,
            "val": val,
            "va_prices": va_prices,
            "hvn": hvn,
            "lvn": lvn,
            "ib": {"high": ib_high, "low": ib_low} if ib_high and ib_low else None,
            "rates_count": len(rates),
            "by": by,
            "block": block,
            "va_percent": va_percent,
            "timeframe": timeframe,
        }
