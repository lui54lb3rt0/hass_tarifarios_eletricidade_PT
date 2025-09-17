import requests
import zipfile
import io
import os
import pandas as pd
from lxml import html

def download_and_extract_zip(zip_url, extract_to):
    """Download ZIP from URL and extract CSV files."""
    print(f"Downloading ZIP from: {zip_url}")
    response = requests.get(zip_url)
    response.raise_for_status()
    if not zip_url.lower().endswith('.zip'):
        print("Warning: The URL does not end with .zip")
    if response.content[:2] != b'PK':
        print("Error: The downloaded file does not look like a ZIP. First bytes:", response.content[:100])
        raise zipfile.BadZipFile("Downloaded file is not a ZIP archive")
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(extract_to)
        return [os.path.join(extract_to, name) for name in z.namelist() if name.endswith('.csv')]

def analyze_csv(csv_path):
    df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip')
    print(f"Summary for {csv_path}:")
    print(df.describe())

def join_and_pivot(cond_path, precos_path):
    cond_df = pd.read_csv(cond_path, sep=';', on_bad_lines='skip')
    precos_df = pd.read_csv(precos_path, sep=';', on_bad_lines='skip')
    merged_df = pd.merge(cond_df, precos_df, on='COD_Proposta', how='inner')
    pivot = merged_df.pivot_table(index='COD_Proposta', aggfunc='size')
    print("Merged DataFrame head:")
    print(merged_df.head())
    print("Pivot Table:")
    print(pivot)
    return merged_df, pivot

def get_zip_link_from_xpath(page_url, xpath):
    response = requests.get(page_url)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    zip_link = tree.xpath(xpath)
    if zip_link:
        href = zip_link[0].get('href') if hasattr(zip_link[0], 'get') else zip_link[0]
        print(f"Extracted href from XPath: {href}")
        if not href.startswith('http'):
            href = page_url.rstrip('/') + '/' + href.lstrip('/')
        print(f"Final ZIP URL: {href}")
        return href
    raise ValueError('ZIP link not found with the given XPath')

def get_csv_link_and_label(page_url):
    response = requests.get(page_url)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    anchor = tree.xpath('//a[contains(@class, "csvPath")]')
    if anchor:
        href = anchor[0].get('href')
        label = anchor[0].xpath('.//span')[0].text_content().strip() if anchor[0].xpath('.//span') else anchor[0].text_content().strip()
        print(f"Extracted href: {href}")
        print(f"Extracted label: {label}")
        if not href.startswith('http'):
            href = page_url.rstrip('/') + '/' + href.lstrip('/')
        return href, label
    raise ValueError('CSV anchor not found on the page')

def get_filtered_dataframe(codigos_oferta=None):
    # Download and process the CSVs as before
    zip_url = 'https://simuladorprecos.erse.pt/Admin/csvs/20250915%20162151%20CSV.zip'
    extract_to = './data'
    csv_files = download_and_extract_zip(zip_url, extract_to)
    for csv_file in csv_files:
        analyze_csv(csv_file)
    cond_path = [f for f in csv_files if f.endswith('CondComerciais.csv')][0]
    precos_path = [f for f in csv_files if f.endswith('Precos_ELEGN.csv')][0]
    merged_df, pivot = join_and_pivot(cond_path, precos_path)
    filtered_df = merged_df[merged_df['Fornecimento'] == 'ELE']
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
    gn_columns = [col for col in filtered_df.columns if 'Gás Natural' in col or 'GN' in col]
    filtered_df = filtered_df.drop(columns=gn_columns)
    html_path = './data/output.html'
    filtered_df.to_html(html_path, index=False, escape=False)
    print(f"HTML file exported to {html_path} (filtered, renamed, GN columns removed)")
    # If codigos_oferta is provided, filter by it
    if codigos_oferta is not None and len(codigos_oferta) > 0:
        filtered_df = filtered_df[filtered_df['Código da oferta comercial'].isin(codigos_oferta)]
    return filtered_df

def get_codigos_oferta():
    df = get_filtered_dataframe()
    return sorted(df["Código da oferta comercial"].unique())