# Tarifários Eletricidade PT Home Assistant Integration

This integration automatically downloads, processes, and analyzes commercial electricity offers for Portugal from ERSE's official simulator. It joins and cleans provider CSV data, allowing users to filter by contracted power (Potência contratada) and creates a Home Assistant entity for each offer. Each entity exposes all relevant offer details as attributes, enabling users to compare tariffs and find the best fit for their consumption profile directly in Home Assistant.

## Features
- Downloads and processes official ERSE CSV data
- Joins commercial conditions and price tables
- Filters offers by contracted power (Pot_Cont)
- Removes all columns related to gas (GN)
- Creates a sensor entity for each offer (CODProposta)
- Exposes all offer details as entity attributes
- Enables tariff comparison and selection in Home Assistant

## Installation

1. Copy the `custom_components/hass_tarifarios_eletricidade_pt` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: hass_tarifarios_eletricidade_pt
```

## Files
- `manifest.json`: Integration metadata
- `__init__.py`: Integration setup
- `const.py`: Constants
- `sensor.py`: Example sensor platform

## License
MIT
