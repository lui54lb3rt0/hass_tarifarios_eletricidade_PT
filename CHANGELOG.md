# Changelog

All notable changes to this project will be documented in this file.

## 2.2.1 - 2025-09-22
- Adicionado suporte para logotipo da integração.
- Melhorias na documentação.

## 2.2.0 - 2025-09-22
- Implementado refresh automático diário às 11:00 (hora local).
- Adicionado sistema de agendamento para atualização automática dos dados.
- Sensores atualizam automaticamente com dados frescos do CSV remoto.
- Melhorada gestão de memória e cleanup de callbacks.

## 2.0.1 - 2025-09-22
- Corrigido erro de device_class=timestamp (agora usa datetime nativo em vez de string).

## 2.0.0 - 2025-09-22
- Adicionado pipeline assíncrono (aiohttp + executor) para evitar bloqueio do loop.
- Introduzido `async_process_csv` e remoção de chamadas síncronas `requests`.
- Sensores por oferta agora expõem todas as colunas como atributos normalizados.
- Estado dos sensores convertido para timestamp (device_class=timestamp).
- Logging de debug para inspeção de colunas/linhas.
- Manifest incrementado e adicionado iot_class/integration_type.

## [1.5.0] - 2025-09-17

### Fixed
- Added `async_setup_entry` to `__init__.py` to support config flow setup and resolve integration setup errors.

### Changed
- Incremented version to 1.5.0.

## [1.4.0] - 2025-09-17

### Fixed
- Config flow now correctly creates the entry after selecting Potência contratada (`pot_cont`), allowing setup to complete.

### Changed
- Incremented version to 1.4.0.

## [1.3.0] - 2025-09-17

### Added
- Config flow now presents a dropdown selector for Potência contratada (`pot_cont`) during integration setup.

### Changed
- Incremented version to 1.3.0.

## [1.2.0] - 2025-09-17

### Changed
- Updated README to clarify setup via Integrations UI, not configuration.yaml.
- Improved documentation for installation and configuration steps.

### Fixed
- Minor documentation corrections.

## [1.1.0] - 2025-09-17
### Changed
- Fixed import for SensorEntity to use homeassistant.components.sensor for compatibility
- Integrated DataFrame loading via data_loader module for cleaner entity setup

## [1.0.0] - 2025-09-17
### Added
- Initial release of Tarifários Eletricidade PT Home Assistant integration
- Automatic download and processing of ERSE CSV data
- Joins commercial conditions and price tables
- Filters offers by contracted power (Pot_Cont)
- Removes all columns related to gas (GN)
- Creates a sensor entity for each offer (CODProposta)
- Exposes all offer details as entity attributes
- Enables tariff comparison and selection in Home Assistant
