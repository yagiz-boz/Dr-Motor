# Local dashboard

The dashboard runs on your own computer at http://127.0.0.1:8501. It binds only
to the loopback interface; cloud deployment is not needed. Usage statistics are
disabled in `.streamlit/config.toml`.

## Windows setup

From the repository root, using Python 3.13 (the tested dashboard runtime):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Open http://127.0.0.1:8501 in a browser. Stop the server with Ctrl+C in its
terminal. If this port is already occupied, pass `--server.port 8502` and open
that port instead. The core modules still target Python 3.11+; dashboard
dependency compatibility is verified with Python 3.13.

## Workflow

1. Upload a CSV or choose an existing `.csv` in `data/raw/`. Files must follow
   [the data format](data-format.md). The entire file is validated first.
2. Select a motor, session and motor type from the sidebar. Channel settings
   form a recording-derived profile and are checked with `MotorProfile`.
   These are descriptions of uploaded data, not verified hardware settings.
3. Use General overview for counts, duration, labels and preview. Sensor
   measurements shows one channel at a time with canonical units and UTC time.
   Gaps in sample indices are reported; missing data is not interpolated.
4. Motor profile shows channel configuration. Recording history lists sessions
   in the currently open file; it is not a persistent Motor Passport database.

Uploads are limited to 20 MB. Uploaded files are parsed through the shared CSV
source using a temporary local copy, which is deleted after parsing. No upload
is saved permanently and no measurement is sent to an external service.
Reloads revalidate the selected recording. Profile selections are session-only.

The empty downloadable template contains only headers and is intentionally not
a valid recording until measurements are added. No synthetic motor data is
displayed. The application does not connect to UNO Q, train models, compute FFT,
or invent a diagnosis. It explicitly shows that no model is available.

For responsiveness the chart shows up to the first 10,000 selected-channel
measurements; the table contains the full channel recording. All parsing and
rendering is in memory; the file limit is not a streaming capability.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Dashboard tests use Streamlit's AppTest and run after installing requirements.
