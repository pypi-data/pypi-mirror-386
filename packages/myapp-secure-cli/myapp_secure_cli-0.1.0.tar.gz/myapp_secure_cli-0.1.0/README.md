# myapp — minimal secure CLI demo (test only)

This is a small demo CLI you can install locally and use to test encrypted storage with MongoDB.

**NOT production-ready.** Intended for quick testing.

## Setup

1. Make sure you have Python 3.9+ and MongoDB running locally (or set `MONGO_URI`).

2. Install dev tools (optional) and the package in editable mode:

```bash
# from project root (myapp-project/)
python -m pip install --upgrade pip
python -m pip install build wheel
python -m pip install -e .
```

Initialize the master key (stored in your OS keyring):
```bash
myapp init
```

Add a credential (you will be prompted for the secret):
```bash
myapp add-cred github_token
```

Retrieve a credential (for testing only — prints the secret):
```bash
myapp get-cred github_token
```

Add and list devices:
```bash
myapp add-device aa:bb:cc:dd:ee:ff 192.168.1.42 server-01
myapp list-devices
```

## Environment

- `MONGO_URI` — optional environment variable to point to MongoDB (defaults to mongodb://localhost:27017).

## Warnings & next steps

This demo stores secrets in MongoDB encrypted with a symmetric key stored in your OS keyring. For production:

- Use KMS (AWS KMS / GCP KMS / HashiCorp Vault) or a secure HSM.
- Add authentication and audit logging.
- Rotate keys, protect logs, and never print secrets in plain text.
