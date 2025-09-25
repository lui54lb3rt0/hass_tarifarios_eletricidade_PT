# Tarifários Eletricidade PT (Home Assistant)

Integração custom para carregar, filtrar e expor tarifários de eletricidade (Portugal) como sensores no Home Assistant.

**Versão atual: 2.2.1**

## Funcionalidades

- Download assíncrono (não bloqueante) de:
  - CondComerciais.csv
  - Precos_ELEGN.csv
- Junção automática dos datasets
- **Atualização automática diária às 11:00** (hora local do Home Assistant)
- Filtro por:
  - Potência contratada
  - Lista de códigos de oferta (COD_Proposta)
  - Apenas fornecimento ELE
- Criação de sensores por oferta selecionada:
  - Estado = timestamp da última atualização
  - Nome = NomeProposta (do CSV) ou "Tarifa <código>"
  - Todos os campos do CSV normalizados como atributos
- Normalização de nomes de atributos (snake_case, remoção de acentos e símbolos)
- Suporte a recarregamento sem perda de dados

## Instalação

1. Copiar pasta `custom_components/hass_tarifarios_eletricidade_pt` para o diretório `config/custom_components` do Home Assistant.
2. Confirmar ficheiros:
   - `__init__.py`
   - `manifest.json` (versão 2.2.1)
   - `const.py`
   - `config_flow.py`
   - `sensor.py`
   - `data_loader.py`
   - `logo.png` (opcional)
3. Reiniciar Home Assistant.
4. Adicionar via: Definições → Dispositivos e Serviços → Adicionar Integração → "Tarifários Eletricidade PT".

## Configuração (UI)

Campos obrigatórios:
- **Potência contratada** (ex: `5.75` ou `5,75`)
- **Lista de códigos de oferta** (um ou vários, separados por vírgula)

Após configurar:
- Sensores por oferta: Nome baseado em `NomeProposta`
- Atualização automática: Todos os dias às 11:00

## Atributos dos Sensores de Oferta

Incluem todas as colunas do DataFrame (normalizadas):
- `codigo_original` - Código da oferta
- `nomeproposta` - Nome da proposta
- `potencia_norm` - Potência normalizada (vírgula → ponto)
- `last_refresh_iso` - Timestamp da última atualização
- Demais campos CSV: termos fixos, energia, condições, links, etc.

## Estado dos Sensores

O estado de cada sensor é o timestamp (UTC ISO8601) da última atualização de dados.

## Atualização Automática

- **Frequência**: Diária às 11:00 (hora local do Home Assistant)
- **Processo**: Download dos CSVs → filtros → atualização dos sensores existentes
- **Novos códigos**: Necessário recarregar integração para adicionar

## Utilização em Templates

```yaml
# Estado (timestamp)
{{ states('sensor.tarifa_eniplenitude_01') }}

# Atributo específico
{{ state_attr('sensor.tarifa_eniplenitude_01', 'nomeproposta') }}
{{ state_attr('sensor.tarifa_eniplenitude_01', 'pot_cont') }}

# Todos os atributos
{{ states.sensor.tarifa_eniplenitude_01.attributes }}
```

## Resolução de Problemas

| Problema | Causa provável | Ação |
|----------|----------------|------|
| Poucos atributos | DataFrame filtrado demais | Ativar debug |
| Aviso blocking I/O | Versão antiga | Atualizar para 2.2.1 |
| Sem sensores | Filtro pot_cont incorreto | Verificar formato (vírgula vs ponto) |
| Não atualiza | Hora incorreta | Confirmar timezone do HA |

### Debug

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
```

## Roadmap

- ✅ Atualizações periódicas automáticas
- ✅ Suporte para logotipo
- 🔄 Auto-adição de novos códigos sem reload
- 🔄 Métricas derivadas (melhor preço vs média)
- 🔄 Suporte gás (opcional)

## Versioning

Esta integração segue [Semantic Versioning](https://semver.org/). 

## Licença

Ver `LICENSE`.