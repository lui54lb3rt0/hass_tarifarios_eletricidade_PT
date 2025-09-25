import asyncio
import logging
from datetime import timedelta
from io import StringIO
import pandas as pd
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

# Correct forward-slash raw URLs (no %5C)
COND_COMERCIAIS_URL = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/CondComerciais.csv"
PRECOS_ELEGN_URL    = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/Precos_ELEGN.csv"

CODE_COLS = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
POT_COLS  = ["Potência contratada", "Pot_Cont"]
FORNECIMENTO_COLS = ["Fornecimento", "fornecimento"]

# Header mapping from codes to descriptive names
HEADER_MAPPING = {
    # Precos_ELEGN headers
    "COM": "Comercializador",
    "Pot_Cont": "Potência contratada",
    "Escalao": "Escalão de consumo",
    "ORD": "Operador de rede",
    "COD_Proposta": "Código da oferta comercial",
    "Contagem": "Ciclo de contagem",
    "TF": "Termo fixo (€/dia)",
    "TV|TVFV|TVP": "Termo de energia (€/kWh) - Simples | Fora de Vazio | Ponta",
    "TVV|TVC": "Termo de energia (€/kWh) - Vazio | Cheias",
    "TVVz": "Termo de energia (€/kWh) - Vazio",
    "TFGN": "Termo fixo (€/dia) - Gás Natural",
    "TVGN": "Termo de energia (€/kWh) - Gás Natural",
    
    # CondComerciais headers
    "CODProposta": "Código da oferta comercial",
    "NomeProposta": "Nome da oferta comercial",
    "TxTModalidade": "Texto auxiliar",
    "Segmento": "Segmento da oferta comercial",
    "TipoContagem": "Ciclos de contagem com oferta - 1 = Simples | 2 = Bi-horária | 3 = Tri-horária | ex: 12 = Simples e Bi-horária; 123 = Simples, Bi-horária e Tri-horária",
    "ConsIni_GN": "Limitações da oferta - Consumo inicial (Gás Natural)",
    "ConsFim_GN": "Limitações da oferta - Consumo final (Gás Natural)",
    "ConsIni_ELE": "Limitações da oferta - Consumo inicial (Eletricidade)",
    "ConsFim_ELE": "Limitações da oferta - Consumo final (Eletricidade)",
    "Fornecimento": "Tipo de energia - Eletricidade | Gás Natural | Dual",
    "DuracaoContrato": "Duração do contrato (meses)",
    "Data ini": "Data de início da oferta comercial",
    "Data fim": "Data de fim da oferta comercial",
    "FiltroContratacao": "Modo de contratação - Eletrónica|Presencial|Telefónica. Ex: 110 = Eletrónica e Presencial; 100 = Eletrónica; 111 = Eletrónica, Presencial e telefónica",
    "Filtrofaturacao": "Modo de faturação - Eletrónica | Papel. Ex: 10 = Eletrónica; 01 = Papel; 11 = Eletrónica e Papel",
    "FiltroPagamento": "Modo de pagamento - Débito direto | Multibanco | Numerário/Payshop/CTT. Ex: 100 = Débito Direto; 101 = Débito direto e Numerário/Payshop/CTT",
    "FiltroAtendimento": "Modo de atendimento - Escrito | Presencial | Telefónico | Eletrónico. Ex: 1000 = Escrito; 1001 = Escrito e Eletrónico; 1101 = Escrito,  Presencial e Eletrónico",
    "FiltroFidelização": "Tem fidelização? (Sim/Não)",
    "FiltroRenovavel": "Tem origem 100% renovável? (Sim/Não)",
    "FiltroRestrições": "Tem restrições? (Sim/Não)",
    "FiltroPrecosIndex": "Tem preços indexados? (Sim/Não)",
    "FiltroServicosAdic": "Tem serviços adicionais obrigatórios? (Sim/Não)",
    "FiltroTarifaSocial": "Tem tarifa social? (Sim/Não)",
    "FiltroReembolsos": "Os desconto/reembolsos aplicam-se a Todos os Clientes da carteira? (Sim/Não)",
    "FiltroNovosClientes": "Os desconto/reembolsos aplicam-se exclusivamente a Novos Clientes da carteira? (Sim/Não)",
    "CustoServicos_s/IVA (€/ano)": "Custo dos serviços adicionais (sem IVA) em €/ano",
    "CustoServicos_c/IVA (€/ano)": "Custo dos serviços adicionais (com IVA) em €/ano",
    "ReembFixo (€/ano)": "Reembolsos/Descontos - Fixos em €/ano (aplicável a Todos os Clientes)",
    "ReembTF_ELE (%)": "Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Eletricidade (aplicável a Todos os Clientes)",
    "ReembTW_ELE (%)": "Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Eletricidade (aplicável a Todos os Clientes)",
    "ReembW_ELE (€/kWh)": "Reembolsos/Descontos sobre o termo de energia (€/kWh) - Eletricidade (aplicável a Todos os Clientes)",
    "ReembTF_GN (%)": "Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Gás Natural (aplicável a Todos os Clientes)",
    "ReembTW_GN (%)": "Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Gás Natural (aplicável a Todos os Clientes)",
    "ReembW_GN (€/kWh)": "Reembolsos/Descontos sobre o termo de energia (€/kWh) - Gás Natural (aplicável a Todos os Clientes)",
    "TxTOferta": "Descritivo da oferta comercial",
    "TxTERSE": "Comentários da ERSE sobre a oferta comercial",
    "LinkCOM": "Link eletrónico para página do comercializador",
    "LinkOfertaCom": "Link eletrónico para a oferta comercial",
    "LinkFichaPadrao": "Link eletrónico para a ficha padronizada",
    "LinkCondicoesGerais": "Link eletrónico para as condições gerais do contrato",
    "ContactoComercialTel": "Contacto telefónico comercial",
    "ContactoWEBouMAIL": "Contacto de email",
    "Contrat_Elect": "Link eletrónico para contratação eletrónica",
    "Contrat_Presen": "Link eletrónico para contratação presencial",
    "Contrat_Telef": "Link eletrónico para contratação telefónica",
    "TxTContratação": "Descritivo no modo de contratação",
    "TxTFatura": "Descritivo no modo de faturação",
    "TxTPagamento": "Descritivo no modo de pagamento",
    "TxTAtendimento": "Descritivo no modo de atendimento",
    "TxTFaturacao": "Descritivo do tipo de faturação (mensal, conta certa…)",
    "TxTFidelização": "Descritivo das condições de fidelização",
    "TxTRestricoesAdic": "Descritivo das restrições adicionais da oferta comercial",
    "Detalhe restrições": "Detalhe das restrições adicionais da oferta comercial",
    "DetalheOutrosDesc/benefi": "Detalhe dos descontos ou benefícios da oferta comercial",
    "TxTAtualizaPrecos": "Descritivo das condições de atualização dos preços da oferta comercial",
    "TxTServicoAdic": "Descritivo das condições dos serviços adicionais obrigatórios da oferta comercial",
    "TxToutrosServicoAdic": "Descritivo das condições de outros serviços adicionais não obrigatórios da oferta comercial",
    "TxTReembolsos": "Descritivo das condições de descontos/reembolsos da oferta comercial",
    "DescontNovoCliente_c/IVA (€/ano)": "Reembolsos/Descontos - Fixos em €/ano (aplicável a Novos Clientes)",
    "Desc. TF_ELE (%) - Novo Cliente": "Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Eletricidade  (aplicável a Novos Clientes)",
    "Desc. TW_ELE (%) - Novo Cliente": "Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Eletricidade  (aplicável a Novos Clientes)",
    "Desc. W_ELE (€/kWh) - Novo Cliente": "Reembolsos/Descontos sobre o termo de energia (€/kWh) - Eletricidade (aplicável a Novos Clientes)",
    "Desc. TF_GN (%) - Novo Cliente": "Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Gás Natural (aplicável a Novos Clientes)",
    "Desc. TW_GN (%) - Novo Cliente": "Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Gás Natural (aplicável a Novos Clientes)",
    "Desc. W_GN (€/kWh) - Novo Cliente": "Reembolsos/Descontos sobre o termo de energia (€/kWh) - Gás Natural (aplicável a Novos Clientes)",
}

def _normalize_pot_val(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(",", ".", regex=False).str.strip()

def _apply_header_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Apply header mapping to convert code headers to descriptive names."""
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_mapped = df.copy()
    
    # Apply mapping to column names
    new_columns = []
    for col in df_mapped.columns:
        mapped_name = HEADER_MAPPING.get(col, col)
        new_columns.append(mapped_name)
    
    df_mapped.columns = new_columns
    _LOGGER.debug("Applied header mapping. Original: %s -> Mapped: %s", 
                  list(df.columns), list(df_mapped.columns))
    
    return df_mapped


async def async_get_comercializadores(hass: HomeAssistant) -> list[str]:
    """Get list of available comercializadores from the data."""
    try:
        df = await async_process_csv(hass, codigos_oferta=None)
        if df.empty:
            _LOGGER.warning("No data available to extract comercializadores")
            return []
        
        # Look for the comercializador column (mapped name)
        comercializador_col = "Comercializador"
        if comercializador_col not in df.columns:
            _LOGGER.warning("Comercializador column not found in data")
            return []
        
        # Get unique comercializadores, sorted
        comercializadores = sorted(df[comercializador_col].dropna().unique().tolist())
        _LOGGER.debug("Found %d comercializadores: %s", len(comercializadores), comercializadores)
        return comercializadores
    
    except Exception as e:
        _LOGGER.error("Error extracting comercializadores: %s", e)
        return []

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

async def async_process_csv(hass: HomeAssistant, codigos_oferta=None, comercializador=None) -> pd.DataFrame:
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

    # Apply header mapping to convert code headers to descriptive names
    cond_df = _apply_header_mapping(cond_df)
    precos_df = _apply_header_mapping(precos_df)

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

    # Filter by comercializador
    if comercializador:
        comercializador_col = "Comercializador"
        if comercializador_col in merged.columns:
            before = len(merged)
            merged = merged[merged[comercializador_col] == comercializador]
            _LOGGER.debug("Comercializador filter '%s': %d -> %d", comercializador, before, len(merged))
        else:
            _LOGGER.warning("Comercializador column not found for comercializador filter.")

    merged = merged.reset_index(drop=True)
    _LOGGER.debug("Final DF rows=%d cols=%d", len(merged), len(merged.columns))
    return merged


class TarifariosDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tarifarios data from GitHub."""

    def __init__(self, hass: HomeAssistant, comercializador=None, codigos_oferta=None):
        """Initialize."""
        self.comercializador = comercializador
        self.codigos_oferta = codigos_oferta
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"Tarifarios {comercializador or 'Eletricidade PT'}",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(hours=24),  # Update once per day
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            _LOGGER.debug("Fetching data from GitHub URLs for %s...", self.comercializador or "all")
            data = await async_process_csv(
                self.hass, 
                codigos_oferta=self.codigos_oferta,
                comercializador=self.comercializador
            )
            if data is None or data.empty:
                raise UpdateFailed("Failed to fetch data or data is empty")
            _LOGGER.info("Successfully fetched %d records from GitHub for %s", 
                        len(data), self.comercializador or "all")
            return data
        except Exception as exception:
            _LOGGER.error("Error fetching data: %s", exception)
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception