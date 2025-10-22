import MetaTrader5 as mt5
import pandas as pd

from mtcli.logger import setup_logger
from mtcli.mt5_context import mt5_conexao

log = setup_logger()


def calcular_rvo(
    symbol: str,
    timeframe: int,
    periodos: int = 20,
    historico: int = 5,
    tipo_volume: str = "tick",
):
    """Calcula o indicador de Volume Relativo (RVO)."""
    with mt5_conexao():
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, periodos + historico)
        if rates is None or len(rates) == 0:
            log.error(f"Sem dados de candles para {symbol}.")
            return None

    df = pd.DataFrame(rates)
    if df.empty:
        return None

    # Seleciona o tipo de volume com fallback para tick_volume
    vol_col = "tick_volume"
    if tipo_volume == "real":
        if "real_volume" in df.columns:
            vol_col = "real_volume"
        else:
            log.warning(f"Volume real não disponível para {symbol}; usando tick_volume.")
            vol_col = "tick_volume"

    df["media_volume"] = df[vol_col].rolling(window=periodos).mean()
    df["rvo"] = df[vol_col] / df["media_volume"]

    # Dados recentes
    ultimo = df.iloc[-1]
    historico_data = df.tail(historico).to_dict(orient="records")

    return {
        "symbol": symbol,
        "volume_tipo": tipo_volume,
        "volume_atual": float(ultimo[vol_col]),
        "volume_medio": float(ultimo["media_volume"]) if pd.notna(ultimo["media_volume"]) else 0.0,
        "rvo_atual": float(ultimo["rvo"]) if pd.notna(ultimo["rvo"]) else 0.0,
        "historico": [
            {"time": int(r["time"]), "rvo": float(r["rvo"]) if pd.notna(r["rvo"]) else 0.0} for r in historico_data
        ],
    }
