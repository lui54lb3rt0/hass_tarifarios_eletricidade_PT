# Changelog

All notable changes to this project will be documented in this file.

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
