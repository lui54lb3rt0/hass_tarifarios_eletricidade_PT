import asyncio
from io import StringIO
import pandas as pd
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

COND_COMERCIAIS_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/CondComerciais.csv"
PRECOS_ELEGN_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/Precos_ELEGN.csv"

# Keep (or expand) your column_map if you want renaming; for now keep raw to show all attributes.
# column_map = {...}

async def _async_fetch_text(hass: HomeAssistant, url: str) -> str:
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=30) as resp:
        resp.raise_for_status()
        return await resp.text()

async def _async_read_csv(hass: HomeAssistant, csv_text: str) -> pd.DataFrame:
    # Run pandas in executor to avoid blocking
    return await asyncio.to_thread(pd.read_csv, StringIO(csv_text), sep=';', dtype=str, na_filter=True)

async def async_process_csv(hass: HomeAssistant, codigos_oferta=None) -> pd.DataFrame:
    cond_text, precos_text = await asyncio.gather(
        _async_fetch_text(hass, COND_COMERCIAIS_URL),
        _async_fetch_text(hass, PRECOS_ELEGN_URL),
    )

    cond_df, precos_df = await asyncio.gather(
        _async_read_csv(hass, cond_text),
        _async_read_csv(hass, precos_text),
    )

    # Basic sanity
    if cond_df.empty:
        return cond_df
    if precos_df.empty:
        # Return only cond if prices missing
        merged = cond_df.copy()
    else:
        # Try common code columns
        code_cols_cond = [c for c in ["COD_Proposta", "CODProposta", "Código da oferta comercial"] if c in cond_df.columns]
        code_cols_prec = [c for c in ["COD_Proposta", "CODProposta", "Código da oferta comercial"] if c in precos_df.columns]
        if not code_cols_cond or not code_cols_prec:
            merged = cond_df
        else:
            merged = cond_df.merge(
                precos_df,
                left_on=code_cols_cond[0],
                right_on=code_cols_prec[0],
                how="left",
                suffixes=("", "_preco")
            )

    # Optional: filter only electricity offers if column exists
    for col in ["Fornecimento", "fornecimento"]:
        if col in merged.columns:
            merged = merged[merged[col].str.upper().fillna("") == "ELE"]
            break

    # Filter by selected offer codes
    if codigos_oferta:
        # Normalize selection
        sel = {c.strip() for c in codigos_oferta if c.strip()}
        code_col = next((c for c in ["Código da oferta comercial", "COD_Proposta", "CODProposta"] if c in merged.columns), None)
        if code_col:
            merged = merged[merged[code_col].isin(sel)]

    # Do NOT drop columns: return everything so sensor picks all attributes
    merged = merged.reset_index(drop=True)
    return merged