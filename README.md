# Tarifários Eletricidade PT (Home Assistant)

Integração custom para carregar, filtrar e expor tarifários de eletricidade (Portugal) como sensores no Home Assistant.

## Funcionalidades

- Download assíncrono (não bloqueante) de:
  - CondComerciais.csv
  - Precos_ELEGN.csv
- Junção automática dos datasets
- Filtro por:
  - Potência contratada
  - Lista de códigos de oferta (COD_Proposta)
  - Apenas fornecimento ELE
- Criação de:
  - 1 sensor resumo (estado = timestamp última atualização)
  - 1 sensor por oferta selecionada (estado = timestamp; todos os campos do CSV normalizados como atributos)
- Normalização de nomes de atributos (snake_case, remoção de acentos e símbolos)
- Suporte a recarregamento removendo e readicionando a integração

## Instalação

1. Copiar pasta `custom_components/hass_tarifarios_eletricidade_pt` para o diretório `config/custom_components` do Home Assistant.
2. Confirmar ficheiros:
   - `__init__.py`
   - `manifest.json`
   - `const.py`
   - `config_flow.py`
   - `sensor.py`
   - `data_loader.py`
3. Reiniciar Home Assistant.
4. Adicionar via: Definições → Dispositivos e Serviços → Adicionar Integração → “Tarifários Eletricidade PT”.

## Configuração (UI)

Campos:
- Potência contratada (ex: `5.75`)
- Lista de códigos de oferta (um ou vários)

Após concluir:
- Sensor resumo: `sensor.tarifarios_electricidade_pt`
- Sensores por oferta: `sensor.tarifa_<COD_Proposta>`

## Atributos dos Sensores de Oferta

Incluem todas as colunas resultantes do DataFrame (normalizadas):
- codigo_original
- pot_cont_raw
- last_refresh
- demais campos (termos fixos, energia, condições, links, etc.)

## Estado dos Sensores

O estado de cada sensor (resumo e ofertas) é o carimbo temporal (UTC ISO8601) da última atualização.

## Atualização

Para aplicar alterações de código:
1. Atualizar ficheiros
2. Incrementar `version` em `manifest.json`
3. Reiniciar Home Assistant
4. Se necessário, remover e readicionar a integração

## Resolução de Problemas

| Problema | Causa provável | Ação |
|----------|----------------|------|
| Só vejo poucos atributos | DataFrame filtrado demais | Ativar debug (ver abaixo) |
| Aviso de blocking I/O | Uso antigo de requests | Já corrigido (usa aiohttp + executor) |
| Sem sensores de oferta | Filtro pot_cont removeu todas as linhas | Verificar valor configurado |

### Debug

Adicionar em `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.hass_tarifarios_eletricidade_pt: debug
```

Reiniciar e verificar Logs → procurar por “async_process_csv”.

## Roadmap

- Atualizações periódicas (DataUpdateCoordinator)
- Métrica derivada (melhor preço vs média)
- Suporte gás (opcional)

## Licença

Ver `LICENSE`.
