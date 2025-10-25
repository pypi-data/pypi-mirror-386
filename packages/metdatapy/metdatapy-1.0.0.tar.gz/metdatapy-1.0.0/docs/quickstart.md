# Quickstart

## Install (editable)

```bash
python -m pip install -e .
```

## Detect and save a mapping

**Option 1: Interactive wizard** (recommended for first-time use)
```bash
mdp ingest detect --csv path/to/file.csv --save mapping.yml
```
This launches an interactive wizard that lets you review and refine auto-detected column mappings. You can press Enter to accept defaults or type custom values.

**Option 2: Non-interactive** (auto-accept detected mappings)
```bash
mdp ingest detect --csv path/to/file.csv --save mapping.yml --yes
```

## Apply mapping and run QC

```bash
mdp ingest apply --csv path/to/file.csv --map mapping.yml --out raw.parquet
mdp qc run --in raw.parquet --out clean.parquet --report qc_report.json
```

## Python API

```python
from metdatapy.mapper import Mapper
from metdatapy.core import WeatherSet
import pandas as pd

mapping = Mapper.load("mapping.yml")
df = pd.read_csv("path/to/file.csv")
ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
ws = ws.insert_missing().fix_accum_rain().qc_range()
ws = ws.derive(["dew_point", "vpd"]).resample("1H")
ws = ws.calendar_features()
clean = ws.to_dataframe()
```
