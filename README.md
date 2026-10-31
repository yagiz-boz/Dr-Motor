# Dr. Motor

AI-powered motor condition monitoring and anomaly detection using Arduino UNO Q.

## Status

Python project scaffold with validated sensor records, CSV storage, and a
source-independent sensor interface with a working CSV adapter.
Motor profiles and model input/output contracts are defined without trained models.
Hardware acquisition, FFT processing, machine learning, and the dashboard
are planned for later stages and are not implemented yet.

## Project structure

```text
Dr-Motor/
├── README.md
├── .gitignore
├── requirements.txt
├── src/          # Sensor record validation and CSV data manager
├── data/         # Local motor measurements (ignored by Git)
├── models/       # Local trained model artifacts (ignored by Git)
├── dashboard/    # Future dashboard code
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

No third-party dependencies are required at this stage. There is no application
entry point yet. See [the data format and usage example](docs/data-format.md)
for the data management API and [sensor sources](docs/sensor-interface.md)
for reading records through the shared interface. Measurement files in `data/raw/` and
`data/processed/` are excluded from Git.

See [motor profiles and model contracts](docs/motor-profile.md) for configuration,
ordered features, and explicit unavailable-model/data outcomes.

## Verification

Run the standard-library test suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```

## Next step

Build the dashboard skeleton around the shared data/profile contracts. Connect
Arduino UNO Q through a new sensor source adapter when hardware is available.
