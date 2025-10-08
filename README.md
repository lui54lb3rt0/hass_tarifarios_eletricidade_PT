# 📊 Tarifários de Eletricidade PT para Home Assistant

[![versão](https://img.shields.io/badge/vers%C3%A3o-2.5.0-blue.svg)](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT)
[![hacs_badge](https://img.shields.io/badge/HACS-Personalizado-orange.svg)](https://github.com/custom-components/hacs)
[![Licença](https://img.shields.io/github/license/lui54lb3rt0/hass_tarifarios_eletricidade_PT.svg)](LICENSE)

> 🇵🇹 **Integração não oficial para tarifários de eletricidade portugueses no Home Assistant**

Integração personalizada avançada que liga o Home Assistant diretamente aos dados oficiais da **ERSE** (Entidade Reguladora dos Serviços Energéticos), permitindo monitorização em tempo real dos tarifários de eletricidade em Portugal.

## ✨ Funcionalidades Principais

### 🔄 **Sincronização Automática com a ERSE**
- **Transferência inteligente**: Descoberta automática de URLs através de análise HTML
- **Dados oficiais**: Liga diretamente ao simulador da ERSE (`simuladorprecos.erse.pt`)
- **Atualização diária**: Sincronização automática às 11:00 (hora local)
- **Sistema robusto**: Múltiplas estratégias de descoberta de dados com redundância

### 📈 **Processamento Avançado de Dados**
- **Junção automática**: CondComerciais.csv + Precos_ELEGN.csv
- **Filtros inteligentes**: Por potência contratada, códigos de oferta e tipo de energia
- **Tipos de energia suportados**: Eletricidade, Gás Natural, ofertas Duais ou todos os tipos
- **Limpeza de dados**: Remove ofertas desnecessárias, normaliza valores automaticamente
- **Agregação**: Uma entidade por oferta com dados de todos os ciclos de faturação

### 🏠 **Integração Nativa no Home Assistant**
- **Config Flow**: Configuração através da interface gráfica
- **Sensores dinâmicos**: Um sensor por oferta tarifária
- **Atributos completos**: Todas as condições comerciais como atributos da entidade
- **Recarregamento**: Suporte total sem perda de dados ou configurações

### 🎨 **Interface Profissional**
- **Logótipo oficial**: Integração com marca própria na lista de integrações
- **Controlo de versões**: Sistema de versões semântico para atualizações
- **Documentação**: Guias completos e resolução de problemas

## 🚀 Instalação

### Método 1: HACS (Recomendado)
1. **Adicionar repositório personalizado**:
   - HACS → Integrações → ⋮ → Repositórios personalizados
   - URL: `https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT`
   - Categoria: Integração

2. **Instalar**:
   - HACS → Integrações → Procurar "Tarifários Eletricidade PT"
   - Transferir e reiniciar o Home Assistant

### Método 2: Instalação Manual
1. **Transferir ficheiros**:
   ```bash
   cd /config/custom_components
   git clone https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT.git hass_tarifarios_eletricidade_pt
   ```

2. **Estrutura de ficheiros**:
   ```
   custom_components/hass_tarifarios_eletricidade_pt/
   ├── __init__.py
   ├── manifest.json
   ├── const.py
   ├── config_flow.py
   ├── sensor.py
   ├── data_loader.py
   ├── downloader.py
   ├── logo.png
   └── icon.png
   ```

3. **Reiniciar o Home Assistant**

## ⚙️ Configuração

### Configuração Inicial
1. **Adicionar Integração**:
   - Definições → Dispositivos e Serviços → Adicionar Integração
   - Procurar "Tarifários Eletricidade PT"

2. **Configurar Parâmetros**:

   **⚡ Tipo de Energia** (obrigatório)
   - `Eletricidade apenas`: Apenas ofertas de eletricidade (padrão)
   - `Gás Natural apenas`: Apenas ofertas de gás natural
   - `Eletricidade e Gás Natural`: Ofertas duais (eletricidade + gás)
   - `Todos os tipos`: Todas as ofertas disponíveis

   **🔌 Potência Contratada** (obrigatório)
   - Formato aceito: `5.75` ou `5,75`
   - Exemplos comuns: `3.45`, `5.75`, `6.90`, `10.35`, `13.80`

   **📋 Códigos de Oferta** (opcional)
   - Um ou vários códigos separados por vírgula
   - Exemplo: `ENIHD.RE.DD.VE.CG.01, GALPENERGIADOMESTICOREGIME1`
   - Deixar vazio para carregar todas as ofertas disponíveis para o tipo de energia selecionado

### Resultado da Configuração
- **Sensores criados**: Um por cada oferta tarifária
- **Nome do sensor**: Baseado em `NomeProposta` do CSV oficial
- **Atualização**: Automática diariamente às 11:00

## 📊 Dados e Sensores

### Estado dos Sensores
- **Estado**: Timestamp da última sincronização (formato ISO8601 UTC)
- **Nome**: Nome comercial da oferta (ex: "ENI Plenitude Regime Especial")
- **ID único**: Baseado no código da oferta para evitar duplicação

### Atributos Disponíveis (Exemplos)
```yaml
# Informações básicas
codigo_original: "ENIPLENITUDE_01"
nomeproposta: "ENI Plenitude Regime Especial"
comercializador: "ENI Plenitude"
escalao: "1"

# Condições comerciais
termo_fixo_power: "5.95"  # €/kW/mês
energia_vazio_normal: "0.1425"  # €/kWh
energia_ponta: "0.2156"  # €/kWh
energia_cheia: "0.1598"  # €/kWh

# Metadados
potencia_norm: "5.75"
last_refresh_iso: "2025-10-07T11:00:00Z"
ciclo_faturacao: "Mensal, Bimestral"
```

### Utilização em Modelos e Automatizações

#### **💡 Modelo Básico**
```yaml
# Estado (última atualização)
{{ states('sensor.eni_plenitude_regime_especial') }}

# Preço da energia no vazio normal
{{ state_attr('sensor.eni_plenitude_regime_especial', 'energia_vazio_normal') }} €/kWh

# Nome comercial
{{ state_attr('sensor.eni_plenitude_regime_especial', 'nomeproposta') }}
```

#### **📈 Comparação de Tarifários**
```yaml
# Modelo para encontrar a tarifa mais barata no vazio normal
{% set ns = namespace(min_price=999, best_tariff="") %}
{% for state in states.sensor %}
  {% if 'tarifarios_eletricidade' in state.entity_id %}
    {% set price = state.attributes.energia_vazio_normal | float(999) %}
    {% if price < ns.min_price %}
      {% set ns.min_price = price %}
      {% set ns.best_tariff = state.attributes.nomeproposta %}
    {% endif %}
  {% endif %}
{% endfor %}
Melhor tarifa: {{ ns.best_tariff }} ({{ ns.min_price }} €/kWh)
```

#### **🔔 Automatização de Notificação**
```yaml
automation:
  - alias: "Notificar Atualização Tarifários"
    trigger:
      platform: state
      entity_id: sensor.eni_plenitude_regime_especial
    action:
      service: notify.mobile_app
      data:
        title: "Tarifários Atualizados"
        message: >
          Nova atualização dos tarifários às 
          {{ trigger.to_state.state | as_timestamp | timestamp_custom('%H:%M') }}
```

## 🛠️ Funcionalidades Avançadas

### Atualização Automática
- **Horário**: Diariamente às 11:00 (hora local)
- **Processo**:
  1. Análise da página oficial da ERSE
  2. Descoberta automática dos URLs dos ficheiros CSV
  3. Transferência dos ficheiros atualizados
  4. Processamento e aplicação de filtros
  5. Atualização dos sensores existentes

### Sistema de Registos
```yaml
# configuration.yaml - Para diagnóstico
logger:
  default: warning
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
    custom_components.hass_tarifarios_eletricidade_pt.downloader: info
```

### Recarregamento da Integração
- **Sem perda de dados**: Recarregar mantém o histórico
- **Novos códigos**: Adicionar códigos requer recarregamento
- **Configuração**: Alterações aplicadas imediatamente

## 🔧 Resolução de Problemas

### Problemas Comuns

| 🚨 Problema | 🔍 Causa Provável | ✅ Solução |
|-------------|-------------------|------------|
| **Poucos ou nenhuns sensores** | Filtro de potência incorreto | Verificar formato: usar `.` em vez de `,` |
| **Aviso "blocking I/O"** | Versão desatualizada | Atualizar para versão 2.4.0+ |
| **Sensores não atualizam** | Timezone incorreto | Confirmar configuração de timezone no HA |
| **Erro de download** | Conexão à ERSE falhada | Verificar conectividade à internet |
| **Múltiplos sensores por oferta** | Versão antiga | Atualizar - versão atual agrupa por oferta |

### Diagnóstico Avançado

#### **📋 Verificar Registos de Diagnóstico**
```yaml
# Ativar registos detalhados
logger:
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
```

#### **🔍 Verificar Estado da Integração**
```yaml
# Modelo para verificar a última atualização
{{ state_attr('sensor.nome_da_sua_tarifa', 'last_refresh_iso') }}

# Verificar se os dados estão atualizados (menos de 25 horas)
{{ (now() - states.sensor.nome_da_sua_tarifa.last_updated).total_seconds() < 90000 }}
```

#### **⚡ Forçar Atualização Manual**
1. Ir a Ferramentas de Programador → Serviços
2. Executar: `homeassistant.reload_config_entry`
3. Selecionar a integração "Tarifários Eletricidade PT"

### Perguntas Frequentes (FAQ)

**P: Posso adicionar novos códigos de oferta sem reconfigurar?**
R: Atualmente é necessário recarregar a integração. A funcionalidade de adição dinâmica está no plano de desenvolvimento.

**P: Os preços incluem taxas e impostos?**
R: Os dados vêm diretamente da ERSE e incluem todos os componentes oficiais do tarifário.

**P: Com que frequência os dados da ERSE são atualizados?**
R: A ERSE atualiza os dados conforme necessário. A integração verifica diariamente.

## 📈 Plano de Desenvolvimento e Funcionalidades Futuras

### ✅ Implementado (v2.5.0)
- ✅ Sincronização automática diária
- ✅ Descoberta inteligente de URLs
- ✅ Sistema robusto de redundância  
- ✅ Agregação por oferta (uma entidade por tarifa)
- ✅ Logótipo e controlo de versões profissional
- ✅ Processamento assíncrono completo
- ✅ **Seleção de tipo de energia** (Eletricidade, Gás Natural, Dual, Todos)
- ✅ **Filtros flexíveis** para diferentes necessidades energéticas

### 🔄 Em Desenvolvimento
- 🔄 Adição dinâmica de ofertas sem recarregamento
- 🔄 Métricas derivadas (comparação automática)
- 🔄 Alertas de mudanças de preços
- 🔄 Painel de controlo pré-configurado

### 🎯 Planeado
- 🎯 Suporte para tarifários de gás natural
- 🎯 Histórico de preços e tendências
- 🎯 Integração com painéis solares
- 🎯 API para outras integrações

## 🤝 Contribuir

### Como Contribuir
1. **Fork** do repositório
2. **Clonar** localmente: `git clone https://github.com/SEU_UTILIZADOR/hass_tarifarios_eletricidade_PT.git`
3. **Branch** para funcionalidade: `git checkout -b funcionalidade/nova-funcionalidade`
4. **Commit** das alterações: `git commit -m "Adicionar nova funcionalidade"`
5. **Push**: `git push origin funcionalidade/nova-funcionalidade`
6. **Pull Request** no GitHub

### Estrutura do Projeto
```
├── custom_components/hass_tarifarios_eletricidade_pt/
│   ├── __init__.py           # Inicialização da integração
│   ├── manifest.json         # Metadados e dependências
│   ├── const.py             # Constantes e configuração
│   ├── config_flow.py       # Interface de configuração
│   ├── sensor.py            # Entidades sensor
│   ├── data_loader.py       # Processamento de dados
│   └── downloader.py        # Transferência e descoberta de URLs
├── README.md                # Esta documentação
├── CHANGELOG.md            # Histórico de versões
└── LICENSE                 # Licença MIT
```

## 📄 Licença e Informações Legais

### Licença
Este projeto está licenciado sob a **Licença MIT** - consulte [LICENSE](LICENSE) para mais detalhes.

### Aviso Legal
- **Dados oficiais**: Esta integração utiliza dados públicos disponibilizados pela ERSE
- **Não oficial**: Não tem afiliação oficial com a ERSE ou outras entidades reguladoras
- **Utilização**: Destinado a fins informativos e domésticos
- **Responsabilidade**: Os utilizadores são responsáveis pela verificação independente dos dados

### Controlo de Versões Semântico
Esta integração segue o [Controlo de Versões Semântico 2.0.0](https://semver.org/):
- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Funcionalidades novas compatíveis
- **PATCH**: Correções de erros compatíveis

---

<div align="center">

**🇵🇹 Feito com ❤️ para a comunidade portuguesa do Home Assistant**

[![GitHub stars](https://img.shields.io/github/stars/lui54lb3rt0/hass_tarifarios_eletricidade_PT.svg?style=social&label=Estrela)](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT)
[![GitHub forks](https://img.shields.io/github/forks/lui54lb3rt0/hass_tarifarios_eletricidade_PT.svg?style=social&label=Fork)](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/fork)

[📖 Documentação](README.md) • [🐛 Reportar Erro](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/issues) • [💡 Sugerir Funcionalidade](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/issues) • [💬 Discussões](https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT/discussions)

</div>