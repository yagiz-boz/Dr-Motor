# Dr. Motor

AI-powered motor condition monitoring and anomaly detection using Arduino UNO Q.

## Status

Initial Python project scaffold. Data acquisition, FFT processing, machine learning,
and the dashboard are planned for later stages and are not implemented yet.

## Project structure

```text
Dr-Motor/
├── README.md
├── .gitignore
├── requirements.txt
├── src/          # Future Python application code
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
entry point yet.

## Next step

Define the Arduino UNO Q data format and acquisition interface before adding
signal processing or model code.
