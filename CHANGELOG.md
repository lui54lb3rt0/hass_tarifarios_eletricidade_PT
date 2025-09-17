# Changelog

All notable changes to this project will be documented in this file.

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
