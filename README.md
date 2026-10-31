# Dr. Motor

AI-powered motor condition monitoring and anomaly detection using Arduino UNO Q.

## Status

Python project scaffold with validated sensor records, CSV storage, and a
source-independent sensor interface with a working CSV adapter.
Motor profiles and model input/output contracts are defined without trained models.
A local Streamlit dashboard supports CSV upload, recording profiles and charts.
Hardware acquisition, FFT processing and machine learning remain future work.

## Project structure

```text
Dr-Motor/
├── README.md
├── .gitignore
├── requirements.txt
├── src/          # Sensor record validation and CSV data manager
├── data/         # Local motor measurements (ignored by Git)
├── models/       # Local trained model artifacts (ignored by Git)
├── dashboard/    # Local Streamlit app
└── experiments/  # Future exploratory work
```

Empty directories contain `.gitkeep` files so Git can track the structure.

## Setup

Use Python 3.11 or newer. From the project directory, create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate` instead.

The core data/profile modules require no third-party dependencies. The dashboard
uses Streamlit and pandas; Python 3.13 is the tested dashboard runtime.
See [the data format and usage example](docs/data-format.md)
for the data management API and [sensor sources](docs/sensor-interface.md)
for reading records through the shared interface. Measurement files in `data/raw/` and
`data/processed/` are excluded from Git.

See [motor profiles and model contracts](docs/motor-profile.md) for configuration,
ordered features, and explicit unavailable-model/data outcomes.

## Local dashboard

After installing requirements, launch from the repository root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Open http://127.0.0.1:8501. See [dashboard usage](docs/dashboard.md) for setup,
file requirements and current limitations.

## Verification

Run the standard-library test suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```

## Next step

Finalize hardware selection and connect Arduino UNO Q through a new sensor
source adapter when hardware is available.
