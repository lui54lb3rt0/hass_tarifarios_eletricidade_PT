# Tarifários Eletricidade PT Home Assistant Integration

This integration allows you to compare electricity tariffs from Portuguese providers and find the best fit for your consumption profile. It automatically downloads, processes, and exposes tariff offers as sensor entities in Home Assistant.

## Installation

1. Copy the `custom_components/hass_tarifarios_eletricidade_pt` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Setup

**Do not add anything to `configuration.yaml`.**

1. Go to **Settings → Devices & Services → Add Integration** in Home Assistant.
2. Search for `Tarifários Eletricidade PT` and follow the setup wizard.
3. Select your contracted power (`Potência contratada`) and other options as prompted.

## Features

- Automatically downloads and processes the latest tariff offers.
- Creates a sensor entity for each offer, with all details as attributes.
- Allows filtering by contracted power during setup.
- Exports filtered offers to HTML for easy viewing.

## Files
- `manifest.json`: Integration metadata
- `__init__.py`: Integration setup
- `sensor.py`: Sensor platform and entity creation
- `data_loader.py`: Data processing and filtering
- `config_flow.py`: UI-based configuration flow

## Changelog

See `CHANGELOG.md` for version history.
