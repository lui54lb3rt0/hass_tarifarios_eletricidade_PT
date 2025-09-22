import asyncio
import logging
from io import StringIO
import pandas as pd
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

COND_COMERCIAIS_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/CondComerciais.csv"
PRECOS_ELEGN_URL    = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/Precos_ELEGN.csv"

CODE_COL_CANDIDATES = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
FORNECIMENTO_COLS   = ["Fornecimento", "fornecimento"]

async def _async_fetch_text(hass: HomeAssistant, url: str) -> str:
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=30) as resp:
        status = resp.status
        text = await resp.text()
        _LOGGER.debug("Fetched %s status=%s size=%d", url, status, len(text))
        resp.raise_for_status()
        return text

async def _async_read_csv(csv_text: str, url_label: str) -> pd.DataFrame:
    # Try ; then , as fallback
    for sep in (";", ","):
        try:
            df = await asyncio.to_thread(pd.read_csv, StringIO(csv_text), sep=sep, dtype=str, na_filter=True)
            if len(df.columns) > 1:
                _LOGGER.debug("%s parsed with sep '%s' rows=%d cols=%s", url_label, sep, len(df), list(df.columns))
                return df
        except Exception as e:
            _LOGGER.debug("%s parse fail sep '%s': %s", url_label, sep, e)
    _LOGGER.warning("%s could not be parsed (returning empty DataFrame).", url_label)
    return pd.DataFrame()

async def async_process_csv(hass: HomeAssistant, codigos_oferta=None) -> pd.DataFrame:
    try:
        cond_text, precos_text = await asyncio.gather(
            _async_fetch_text(hass, COND_COMERCIAIS_URL),
            _async_fetch_text(hass, PRECOS_ELEGN_URL),
        )
    except Exception as e:
        _LOGGER.error("Download failed: %s", e)
        return pd.DataFrame()

    cond_df, precos_df = await asyncio.gather(
        _async_read_csv(cond_text, "CondComerciais"),
        _async_read_csv(precos_text, "Precos_ELEGN"),
    )

    if cond_df.empty:
        _LOGGER.warning("cond_df empty. Stopping.")
        return cond_df

    # Try to detect CODE column early
    code_col_cond = next((c for c in CODE_COL_CANDIDATES if c in cond_df.columns), None)
    code_col_prec = next((c for c in CODE_COL_CANDIDATES if c in precos_df.columns), None)

    if precos_df.empty or not code_col_cond or not code_col_prec:
        _LOGGER.debug(
            "Skipping merge (precos empty=%s, code_col_cond=%s, code_col_prec=%s)",
            precos_df.empty, code_col_cond, code_col_prec
        )
        merged = cond_df.copy()
    else:
        merged = cond_df.merge(
            precos_df,
            left_on=code_col_cond,
            right_on=code_col_prec,
            how="left",
            suffixes=("", "_preco")
        )
        _LOGGER.debug("After merge rows=%d cols=%d", len(merged), len(merged.columns))

    # ELE filter (log unique before/after)
    fornec_col = next((c for c in FORNECIMENTO_COLS if c in merged.columns), None)
    if fornec_col:
        before = len(merged)
        uniques = sorted(set(merged[fornec_col].dropna().unique().tolist()))
        _LOGGER.debug("Fornecimento unique values before filter: %s", uniques)
        merged = merged[merged[fornec_col].str.upper().fillna("").str.strip() == "ELE"]
        _LOGGER.debug("ELE filter rows %d -> %d", before, len(merged))
    else:
        _LOGGER.debug("Fornecimento column not found; skipping ELE filter.")

    if codigos_oferta:
        sel = {c.strip() for c in codigos_oferta if c and c.strip()}
        code_col_final = next((c for c in CODE_COL_CANDIDATES if c in merged.columns), None)
        if code_col_final:
            before_codes = len(merged)
            merged = merged[merged[code_col_final].isin(sel)]
            _LOGGER.debug("Codes filter (%d codes) rows %d -> %d", len(sel), before_codes, len(merged))
        else:
            _LOGGER.warning("Code column not found when applying codes filter. Columns=%s", list(merged.columns))

    if merged.empty:
        _LOGGER.warning("Result empty after filters. Columns at end: %s", list(cond_df.columns))
    else:
        _LOGGER.debug("Final DataFrame rows=%d cols=%d", len(merged), len(merged.columns))

    return merged.reset_index(drop=True)