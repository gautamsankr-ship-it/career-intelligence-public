# Synthetic Application Resolution Portfolio

This repository is a small, public-safe demonstration of grouped application-answer resolution.

It contains only source code, a safe HTML template, synthetic demo data, and tests that use
temporary directories. It deliberately contains no candidate profile, application history,
resume, vault export, database, credential, token, or log.

## Run

```bash
python -m venv .venv
python -m pip install -r requirements.txt
pytest -q
python phase10_demo.py
```

The demo writes its SQLite-compatible test state only inside a temporary directory and deletes
that directory when it exits.

## Safety boundary

All personal-looking values are synthetic placeholders such as `candidate@example.test` and
`Synthetic Company`. Tests use `tmp_path`; no repository-relative runtime storage is used.
