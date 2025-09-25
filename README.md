# Tarifários Eletricidade PT (Home Assistant)

Integração personalizada para Home Assistant que carrega e monitora tarifários de eletricidade portugueses em tempo real, organizados por comercializador e com atualizações automáticas diárias.

## ✨ Funcionalidades

### 🏢 **Organização por Comercializador**
- **Entradas por fornecedor**: Cada comercializador (EDPSU, ACCIONA, ALFAENERGIA, etc.) tem a sua própria entrada
- **Múltiplas configurações**: Pode adicionar várias entradas para o mesmo comercializador com configurações diferentes
- **Títulos claros**: Cada entrada mostra o nome do comercializador

### 🔄 **Atualizações Automáticas**
- **Atualização diária**: Dados são automaticamente atualizados uma vez por dia
- **Fonte GitHub**: Carrega dados diretamente dos ficheiros CSV no repositório GitHub
- **Sem reinicializações**: Sensores atualizam automaticamente sem necessidade de reiniciar

### 🎛️ **Configuração Inteligente**
- **Seleção de Comercializador**: Primeiro escolhe o fornecedor de energia
- **Códigos Dinâmicos**: Mostra apenas os códigos de oferta disponíveis para o comercializador selecionado
- **Filtro por Potência**: Suporta todas as potências contratuais portuguesas (1,15 a 41,4 kVA)

### 📊 **Sensores Detalhados**
- **Nomes Descritivos**: `Comercializador - Nome da Oferta Comercial`
- **Valor Real**: Estado do sensor mostra o "Termo Fixo" diário em €/dia
- **Atributos Completos**: Todos os dados tarifários disponíveis como atributos

## 🚀 Instalação

### Via HACS (Recomendado)
1. Abrir HACS no Home Assistant
2. Ir para "Integrações"
3. Clicar nos três pontos → "Repositórios personalizados"
4. Adicionar: `https://github.com/lui54lb3rt0/hass_tarifarios_eletricidade_PT`
5. Categoria: "Integration"
6. Instalar e reiniciar o Home Assistant

### Manual
1. Descarregar e extrair para: `config/custom_components/hass_tarifarios_eletricidade_pt/`
2. Reiniciar Home Assistant
3. Adicionar via UI: **Definições** → **Integrações** → **Adicionar Integração**

## ⚙️ Configuração

### Passo 1: Escolher Comercializador
Selecione o fornecedor de energia que pretende monitorizar:
- EDPSU (EDP Comercial)
- ACCIONA
- ALFAENERGIA
- AUDAX
- AXPO
- E muitos outros...

### Passo 2: Configurar Parâmetros
- **Potência Contratada**: Escolha a sua potência (formato português: 1,15, 2,3, 3,45, etc.)
- **Códigos de Oferta**: (Opcional) Selecione ofertas específicas ou deixe vazio para todas

## 📈 Sensores Criados

### Formato dos Nomes
```
EDPSU - Tarifa Regulada Eletricidade
ACCIONA - Energia Verde Plus
ALFAENERGIA - Oferta Competitiva Casa
```

### Estado do Sensor
- **Valor**: Termo fixo diário em euros (ex: 0.085)
- **Unidade**: €/day
- **Ícone**: 💶

### Atributos Disponíveis
```yaml
comercializador: "EDPSU"
nome_oferta_comercial: "Tarifa Regulada Eletricidade"
codigo_original: "TUR"
termo_fixo_eur_dia: 0.085
potencia_norm: "3.45"
termo_de_energia_kwh_simples_fora_de_vazio_ponta: 0.1658
# ... todos os outros campos tarifários
last_refresh_iso: "2025-09-25T10:30:00Z"
```

## 🔍 Funcionalidades Avançadas

### Headers Inteligentes
- Converte códigos técnicos em nomes descritivos
- `COM` → `Comercializador`
- `TF` → `Termo fixo (€/dia)`
- `POT_CONT` → `Potência contratada`

### Filtragem Precisa
- **Por Comercializador**: Dados apenas do fornecedor selecionado
- **Por Potência**: Filtragem exata da potência contratual
- **Por Códigos**: Ofertas específicas se desejado

### Coordenação de Dados
- Sistema robusto de atualização com retry automático
- Gestão centralizada de dados por comercializador
- Log detalhado para debugging

## 🛠️ Resolução de Problemas

### Logs de Debug
Adicione ao `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
```

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Não aparecem ofertas para potência selecionada | Verificar se a potência existe para esse comercializador |
| Dados não atualizam | Verificar logs - pode ser problema de conectividade |
| Sensores com nomes estranhos | Normal - usa nomes oficiais das ofertas comerciais |

### Verificação de Estado
Os logs mostram:
- Quantos registos foram carregados
- Filtros aplicados
- Valores de potência disponíveis
- Códigos de oferta encontrados

## 📊 Exemplos de Uso

### Automação - Alertar Melhor Tarifa
```yaml
automation:
  - alias: "Alerta Melhor Tarifa"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Melhor tarifa hoje: 
            {{ states.sensor | selectattr('entity_id', 'match', 'sensor.*edpsu.*') 
               | sort(attribute='state') | first }}
```

### Template Sensor - Comparação
```yaml
template:
  - sensor:
      - name: "Tarifa Mais Barata"
        state: >
          {{ states.sensor | selectattr('attributes.comercializador', 'defined')
             | sort(attribute='state') | first | attr('state') }}
        unit_of_measurement: "€/day"
```

## 🔮 Roadmap

- ✅ **Atualizações Diárias**: Implementado
- ✅ **Organização por Comercializador**: Implementado  
- ✅ **Filtros Inteligentes**: Implementado
- ✅ **Headers Descritivos**: Implementado
- 🔄 **Notificações de Mudanças de Preço**: Em desenvolvimento
- 🔄 **Comparação Automática**: Em desenvolvimento
- 🔄 **Histórico de Preços**: Planeado

## 📝 Changelog

### v2.0.0 (2025-09-25)
- ✨ **Nova arquitetura**: Organização por comercializador
- ✨ **Atualizações automáticas**: Coordenador com updates diários
- ✨ **Configuração inteligente**: Códigos dinâmicos por comercializador
- ✨ **Headers descritivos**: Mapeamento automático de nomes técnicos
- ✨ **Filtros precisos**: Potência exata em formato português
- ✨ **Sensores melhorados**: Estado mostra termo fixo em €/dia
- 🐛 **Filtro de potência**: Corrigido problema de filtragem
- 🐛 **Nomes de entidades**: Formato "Comercializador - Oferta"

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:
1. Fork do repositório
2. Criar branch para a funcionalidade
3. Commit das alterações
4. Push para a branch
5. Criar Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - ver ficheiro [LICENSE](LICENSE) para detalhes.

---

**💡 Dica**: Esta integração é perfeita para quem quer monitorizar e comparar tarifas de eletricidade portuguesas automaticamente no Home Assistant!