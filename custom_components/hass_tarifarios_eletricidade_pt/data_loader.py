import requests
import zipfile
import io
import os
import pandas as pd
from lxml import html

def fetch_csv(url):
    """Fetch a CSV file from a URL and return a pandas DataFrame."""
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text), sep=';', on_bad_lines='skip')

def analyze_csv(df):
    """Print summary statistics for a DataFrame."""
    print(df.describe(include='all'))

def join_and_analyze(cond_url, precos_url):
    """Fetch, join, and analyze CondComerciais and Precos_ELEGN CSVs."""
    cond_df = fetch_csv(cond_url)
    precos_df = fetch_csv(precos_url)
    merged_df = pd.merge(cond_df, precos_df, on='COD_Proposta', how='inner')
    print("Merged DataFrame head:")
    print(merged_df.head())
    analyze_csv(merged_df)
    return merged_df

def export_to_html(df, html_path='./data/output.html'):
    """Export the given DataFrame to an HTML file."""
    df.to_html(html_path, index=False, escape=False)
    print(f"HTML file exported to {html_path}")

def process_csv(codigos_oferta=None):
    cond_url = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/csv%5CCondComerciais.csv"
    precos_url = "https://raw.githubusercontent.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/refs/heads/main/data/csv%5CPrecos_ELEGN.csv"
    cond_df = fetch_csv(cond_url)
    precos_df = fetch_csv(precos_url)
    merged_df = pd.merge(cond_df, precos_df, on='COD_Proposta', how='inner')
    filtered_df = merged_df[merged_df['Fornecimento'] == 'ELE']   
    filtered_df = filtered_df[filtered_df['FiltroContratacao'].isin([100, 110, 111])]
    filtered_df = filtered_df[filtered_df['Pot_Cont'] == '5,75']
    column_map = {
        # Precos_ELEGN
        'COM': 'Comercializador',
        'Pot_Cont': 'Potência contratada',
        'Escalao': 'Escalão de consumo',
        'ORD': 'Operador de rede',
        'COD_Proposta': 'Código da oferta comercial',
        'Contagem': 'Ciclo de contagem',
        'TF': 'Termo fixo (€/dia)',
        'TV': 'Termo de energia (€/kWh) - Simples',
        'TVFV': 'Termo de energia (€/kWh) - Fora de Vazio',
        'TVP': 'Termo de energia (€/kWh) - Ponta',
        'TVV': 'Termo de energia (€/kWh) - Vazio',
        'TVC': 'Termo de energia (€/kWh) - Cheias',
        'TVVz': 'Termo de energia (€/kWh) - Vazio',

        # CondComerciais
        'COM': 'Comercializador',
        'CODProposta': 'Código da oferta comercial',
        'NomeProposta': 'Nome da oferta comercial',
        'TxTModalidade': 'Texto auxiliar',
        'Segmento': 'Segmento da oferta comercial',
        'TipoContagem': 'Ciclos de contagem com oferta - 1 = Simples | 2 = Bi-horária | 3 = Tri-horária | ex: 12 = Simples e Bi-horária; 123 = Simples, Bi-horária e Tri-horária',
        'ConsIni_ELE': 'Limitações da oferta - Consumo inicial (Eletricidade)',
        'ConsFim_ELE': 'Limitações da oferta - Consumo final (Eletricidade)',
        'Fornecimento': 'Tipo de energia - Eletricidade | Gás Natural | Dual',
        'DuracaoContrato': 'Duração do contrato (meses)',
        'Data ini': 'Data de início da oferta comercial',
        'Data fim': 'Data de fim da oferta comercial',
        'FiltroContratacao': 'Modo de contratação - Eletrónica|Presencial|Telefónica. Ex: 110 = Eletrónica e Presencial; 100 = Eletrónica; 111 = Eletrónica, Presencial e telefónica',
        'Filtrofaturacao': 'Modo de faturação - Eletrónica | Papel. Ex: 10 = Eletrónica; 01 = Papel; 11 = Eletrónica e Papel',
        'FiltroPagamento': 'Modo de pagamento - Débito direto | Multibanco | Numerário/Payshop/CTT. Ex: 100 = Débito Direto; 101 = Débito direto e Numerário/Payshop/CTT',
        'FiltroAtendimento': 'Modo de atendimento - Escrito | Presencial | Telefónico | Eletrónico. Ex: 1000 = Escrito; 1001 = Escrito e Eletrónico; 1101 = Escrito,  Presencial e Eletrónico',
        'FiltroFidelização': 'Tem fidelização? (Sim/Não)',
        'FiltroRenovavel': 'Tem origem 100% renovável? (Sim/Não)',
        'FiltroRestrições': 'Tem restrições? (Sim/Não)',
        'FiltroPrecosIndex': 'Tem preços indexados? (Sim/Não)',
        'FiltroServicosAdic': 'Tem serviços adicionais obrigatórios? (Sim/Não)',
        'FiltroTarifaSocial': 'Tem tarifa social? (Sim/Não)',
        'FiltroReembolsos': 'Os desconto/reembolsos aplicam-se a Todos os Clientes da carteira? (Sim/Não)',
        'FiltroNovosClientes': 'Os desconto/reembolsos aplicam-se exclusivamente a Novos Clientes da carteira? (Sim/Não)',
        'CustoServicos_s/IVA (€/ano)': 'Custo dos serviços adicionais (sem IVA) em €/ano',
        'CustoServicos_c/IVA (€/ano)': 'Custo dos serviços adicionais (com IVA) em €/ano',
        'ReembFixo (€/ano)': 'Reembolsos/Descontos - Fixos em €/ano (aplicável a Todos os Clientes)',
        'ReembTF_ELE (%)': 'Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Eletricidade (aplicável a Todos os Clientes)',
        'ReembTW_ELE (%)': 'Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Eletricidade (aplicável a Todos os Clientes)',
        'ReembW_ELE (€/kWh)': 'Reembolsos/Descontos sobre o termo de energia (€/kWh) - Eletricidade (aplicável a Todos os Clientes)',
        'TxTOferta': 'Descritivo da oferta comercial',
        'TxTERSE': 'Comentários da ERSE sobre a oferta comercial',
        'LinkCOM': 'Link eletrónico para página do comercializador',
        'LinkOfertaCom': 'Link eletrónico para a oferta comercial',
        'LinkFichaPadrao': 'Link eletrónico para a ficha padronizada',
        'LinkCondicoesGerais': 'Link eletrónico para as condições gerais do contrato',
        'ContactoComercialTel': 'Contacto telefónico comercial',
        'ContactoWEBouMAIL': 'Contacto de email',
        'Contrat_Elect': 'Link eletrónico para contratação eletrónica',
        'Contrat_Presen': 'Link eletrónico para contratação presencial',
        'Contrat_Telef': 'Link eletrónico para contratação telefónica',
        'TxTContratação': 'Descritivo no modo de contratação',
        'TxTFatura': 'Descritivo no modo de faturação',
        'TxTPagamento': 'Descritivo no modo de pagamento',
        'TxTAtendimento': 'Descritivo no modo de atendimento',
        'TxTFaturacao': 'Descritivo do tipo de faturação (mensal, conta certa…)',
        'TxTFidelização': 'Descritivo das condições de fidelização',
        'TxTRestricoesAdic': 'Descritivo das restrições adicionais da oferta comercial',
        'Detalhe restrições': 'Detalhe das restrições adicionais da oferta comercial',
        'DetalheOutrosDesc/ben': 'Detalhe dos descontos ou benefícios da oferta comercial',
        'TxTAtualizaPrecos': 'Descritivo das condições de atualização dos preços da oferta comercial',
        'TxTServicoAdic': 'Descritivo das condições dos serviços adicionais obrigatórios da oferta comercial',
        'TxToutrosServicoAdic': 'Descritivo das condições de outros serviços adicionais não obrigatórios da oferta comercial',
        'TxTReembolsos': 'Descritivo das condições de descontos/reembolsos da oferta comercial',
        'DescontNovoCliente_c/IVA (€/ano)': 'Reembolsos/Descontos - Fixos em €/ano (aplicável a Novos Clientes)',
        'Desc. TF_ELE (%) - Novo Cliente': 'Reembolsos/Descontos percentuais sobre o Termo Fixo (%) - Eletricidade  (aplicável a Novos Clientes)',
        'Desc. TW_ELE (%) - Novo Cliente': 'Reembolsos/Descontos percentuais sobre o Termo de energia (%) - Eletricidade  (aplicável a Novos Clientes)',
        'Desc. W_ELE (€/kWh) - Novo Cliente': 'Reembolsos/Descontos sobre o termo de energia (€/kWh) - Eletricidade (aplicável a Novos Clientes)',
        'TV4V': 'Tipo de energia (kWh)',
    }
    filtered_df = filtered_df.rename(columns=column_map)
    filtered_df = filtered_df.drop(columns=['Escalão de consumo', 'Operador de rede', 'COM_y'])
    gn_columns = [col for col in filtered_df.columns if 'Gás Natural' in col or 'GN' in col]
    filtered_df = filtered_df.drop(columns=gn_columns)
    if codigos_oferta is not None and len(codigos_oferta) > 0:
        filtered_df = filtered_df[filtered_df['Código da oferta comercial'].isin(codigos_oferta)]
    export_to_html(filtered_df)
    return filtered_df

"""""
if __name__ == "__main__":
    # Example usage: process all offers and export to HTML
    df = process_csv()
    print("Processed DataFrame:")
    print(df.head())
    # Optionally, process only specific offers:
    # selected_codigos = ["12345", "67890"]
    # df_filtered = process_csv(codigos_oferta=selected_codigos)
    # print(df_filtered.head())
"""""