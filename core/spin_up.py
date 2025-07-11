import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import subprocess
import time
from core.rotor_overlay import log_event
from core.rotor_chunk_and_stream import rotor_chunk_and_upload

def fetch_secrets():
    os.system("python3 ~/Soap/core/fetch_secrets_from_mongo.py")
    log_event("spin_up: Pulled secrets from MongoDB.")

def pull_latest_gcs_backup():
    backup_dir = os.path.expanduser("~/Soap/overlay")
    os.makedirs(backup_dir, exist_ok=True)
    list_result = subprocess.run(
        ["gsutil", "ls", "gs://ati-oracle-engine/backups/"],
        capture_output=True, text=True, check=True)
    zips = [line for line in list_result.stdout.splitlines() if line.endswith(".zip")]
    if not zips:
        log_event("spin_up: No backups found in GCS.")
        return None
    latest = sorted(zips)[-1]
    local_zip = os.path.join(backup_dir, os.path.basename(latest))
    subprocess.run(["gsutil", "cp", latest, local_zip], check=True)
    log_event(f"spin_up: Pulled latest backup {latest}")
    return local_zip

def extract_backup(zip_path):
    subprocess.run(["unzip", "-o", zip_path, "-d", os.path.dirname(zip_path)], check=True)
    log_event(f"spin_up: Extracted {zip_path}")

def restore_core():
    fetch_secrets()
    zip_path = pull_latest_gcs_backup()
    if zip_path:
        extract_backup(zip_path)
        log_event("spin_up: Core files restored from GCS.")
    # Trigger chunker after restore
    upload_dir = os.path.expanduser("~/Soap/upload")
    for f in os.listdir(upload_dir):
        fpath = os.path.join(upload_dir, f)
        if os.path.getsize(fpath) > 100 * 1024 * 1024:
            rotor_chunk_and_upload(fpath)

if __name__ == "__main__":
    restore_core()
    time.sleep(2)
    log_event("spin_up: Now launching rotor_fusion.")
    subprocess.Popen(["python3", os.path.expanduser("~/Soap/core/rotor_fusion.py")])
