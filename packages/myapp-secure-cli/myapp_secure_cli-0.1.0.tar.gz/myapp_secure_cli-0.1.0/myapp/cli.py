import os
import sys
import datetime
import getpass
import base64
import json
import typer
from typing import Optional, List
from pymongo import MongoClient
from cryptography.fernet import Fernet
import keyring
from bson import ObjectId

app = typer.Typer(help="myapp — minimal secure CLI demo (test only)")

# Configuration (override with env var MONGO_URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB = MongoClient(MONGO_URI).myapp_db

# Keyring service/name
KEYRING_SERVICE = "myapp"
KEYRING_KEYNAME = "master_key"

def _get_fernet():
    key = keyring.get_password(KEYRING_SERVICE, KEYRING_KEYNAME)
    if not key:
        typer.echo("No master key found. Run: myapp init")
        raise typer.Exit(code=1)
    return Fernet(key.encode())

@app.command()
def init(reset: bool = typer.Option(False, help="Reset existing key if present")):
    """
    Initialize the app by generating and saving a master key in the OS keyring.
    """
    existing = keyring.get_password(KEYRING_SERVICE, KEYRING_KEYNAME)
    if existing and not reset:
        typer.echo("Master key already exists. Use --reset to overwrite.")
        raise typer.Exit()
    key = Fernet.generate_key().decode()
    keyring.set_password(KEYRING_SERVICE, KEYRING_KEYNAME, key)
    typer.echo("✅ Master key generated and stored in OS keyring.")

@app.command()
def add_cred(name: str, tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags")):
    """
    Add an encrypted credential. You will be prompted for the secret.
    """
    secret = getpass.getpass(f"Secret for '{name}': ")
    if not secret:
        typer.echo("Empty secret — aborting.")
        raise typer.Exit()

    f = _get_fernet()
    token = f.encrypt(secret.encode())
    doc = {
        "type": "credential",
        "name": name,
        "token": base64.b64encode(token).decode(),
        "tags": tags or [],
        "created_at": datetime.datetime.utcnow()
    }
    result = DB.items.insert_one(doc)
    typer.echo(f"Saved credential '{name}' (id: {result.inserted_id})")

@app.command()
def get_cred(name: str):
    """
    Retrieve and decrypt a credential by name (for testing).
    """
    doc = DB.items.find_one({"type": "credential", "name": name})
    if not doc:
        typer.echo("❌ Credential not found.")
        raise typer.Exit(code=1)
    token = base64.b64decode(doc["token"])
    f = _get_fernet()
    try:
        plaintext = f.decrypt(token).decode()
    except Exception as e:
        typer.echo("❌ Failed to decrypt secret: " + str(e))
        raise typer.Exit(code=1)
    typer.echo(f"🔓 {name}: {plaintext}")

@app.command()
def add_device(mac: str, ip: str, hostname: Optional[str] = typer.Argument(None)):
    """
    Register a device with mac and ip.
    """
    doc = {
        "type": "device",
        "mac": mac.lower(),
        "ip": ip,
        "hostname": hostname or "",
        "registered_at": datetime.datetime.utcnow()
    }
    result = DB.devices.insert_one(doc)
    typer.echo(f"Device registered (id: {result.inserted_id})")

@app.command()
def list_devices():
    """
    List registered devices.
    """
    cursor = DB.devices.find().sort("registered_at", -1)
    rows = list(cursor)
    if not rows:
        typer.echo("No devices registered.")
        return
    for d in rows:
        rid = str(d.get("_id"))
        mac = d.get("mac")
        ip = d.get("ip")
        hs = d.get("hostname", "")
        ts = d.get("registered_at")
        typer.echo(f"- id={rid} mac={mac} ip={ip} hostname={hs} registered_at={ts}")

if __name__ == "__main__":
    app()
