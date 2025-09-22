import asyncio
import logging
from io import StringIO
import pandas as pd
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Correct forward-slash raw URLs (no %5C)
COND_COMERCIAIS_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/CondComerciais.csv"
PRECOS_ELEGN_URL    = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/Precos_ELEGN.csv"

CODE_COLS = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
POT_COLS  = ["Potência contratada", "Pot_Cont"]
FORNECIMENTO_COLS = ["Fornecimento", "fornecimento"]

def _normalize_pot_val(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(",", ".", regex=False).str.strip()

async def _async_fetch(hass: HomeAssistant, url: str) -> str:
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=30) as resp:
        txt = await resp.text()
        _LOGGER.debug("Fetched %s status=%s size=%d", url, resp.status, len(txt))
        resp.raise_for_status()
        return txt

async def _async_read(csv_text: str, label: str) -> pd.DataFrame:
    # Try ; then ,
    for sep in (";", ","):
        try:
            df = await asyncio.to_thread(pd.read_csv, StringIO(csv_text), sep=sep, dtype=str, na_filter=True)
            if len(df.columns) > 1:
                _LOGGER.debug("%s parsed sep='%s' rows=%d cols=%s", label, sep, len(df), list(df.columns))
                return df
        except Exception as e:
            _LOGGER.debug("%s parse fail sep='%s': %s", label, sep, e)
    _LOGGER.warning("%s empty/unparsable", label)
    return pd.DataFrame()

async def async_process_csv(hass: HomeAssistant, codigos_oferta=None) -> pd.DataFrame:
    try:
        cond_txt, precos_txt = await asyncio.gather(
            _async_fetch(hass, COND_COMERCIAIS_URL),
            _async_fetch(hass, PRECOS_ELEGN_URL),
        )
    except Exception as e:
        _LOGGER.error("Download failure: %s", e)
        return pd.DataFrame()

    cond_df, precos_df = await asyncio.gather(
        _async_read(cond_txt, "CondComerciais"),
        _async_read(precos_txt, "Precos_ELEGN"),
    )

    if cond_df.empty:
        _LOGGER.warning("CondComerciais DataFrame empty.")
        return cond_df

    code_cond = next((c for c in CODE_COLS if c in cond_df.columns), None)
    code_prec = next((c for c in CODE_COLS if c in precos_df.columns), None)

    if precos_df.empty or not code_cond or not code_prec:
        merged = cond_df.copy()
        _LOGGER.debug("Skipping merge (precos empty or code col missing).")
    else:
        merged = cond_df.merge(
            precos_df,
            left_on=code_cond,
            right_on=code_prec,
            how="left",
            suffixes=("", "_preco"),
        )
        _LOGGER.debug("Merged rows=%d cols=%d", len(merged), len(merged.columns))

    # Normalize potencia columns (add a normalized column)
    for pot_col in POT_COLS:
        if pot_col in merged.columns:
            merged[f"{pot_col}__norm"] = _normalize_pot_val(merged[pot_col])

    # Filter ELE (use startswith to be tolerant)
    fornec_col = next((c for c in FORNECIMENTO_COLS if c in merged.columns), None)
    if fornec_col:
        before = len(merged)
        uniques = sorted(set(merged[fornec_col].dropna().str.strip().str.upper()))
        _LOGGER.debug("Fornecimento uniques before: %s", uniques)
        merged = merged[merged[fornec_col].str.upper().fillna("").str.strip().str.startswith("ELE")]
        _LOGGER.debug("ELE filter %d -> %d", before, len(merged))
        if merged.empty:
            _LOGGER.warning("All rows removed by ELE filter. Keeping original (skipping filter).")
            merged = cond_df.copy()

    # Filter by selected codes
    if codigos_oferta:
        sel = {c.strip() for c in codigos_oferta if c and c.strip()}
        code_final = next((c for c in CODE_COLS if c in merged.columns), None)
        if code_final:
            before = len(merged)
            merged = merged[merged[code_final].isin(sel)]
            _LOGGER.debug("Codes filter (%d) %d -> %d", len(sel), before, len(merged))
        else:
            _LOGGER.warning("Code column not found for codes filter.")

    merged = merged.reset_index(drop=True)
    _LOGGER.debug("Final DF rows=%d cols=%d", len(merged), len(merged.columns))
    return merged