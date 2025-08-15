from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import subprocess
import shutil

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from google.oauth2 import service_account  # noqa: F401  # for type hints; ADC used by default
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage


# Minimal duplicate of confidential config loader
def _load_confidential_config() -> Dict[str, Any]:
    candidates = [
        Path(__file__).resolve().parents[2] / "config" / "config_confidential.yaml",
        Path(__file__).resolve().parents[1] / "config" / "config_confidential.yaml",
        Path(__file__).resolve().parent / "config" / "config_confidential.yaml",
    ]
    try:
        import yaml  # local dependency
    except Exception:
        return {}
    for path in candidates:
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    return data
        except Exception:
            continue
    return {}


# OAuth scopes used for both Compute and Storage
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/compute",
]


@dataclass
class GcpVmOffloadSettings:
    project_id: str
    zone: str
    machine_type: str = "e2-standard-4"
    disk_size_gb: int = 50
    image_project: str = "debian-cloud"
    image_family: str = "debian-12"
    service_account_email: Optional[str] = None
    results_bucket: str = ""
    timeout_minutes: int = 60
    service_account_file: Optional[str] = None  # optional fallback path


class GcpVmOffloader:
    def __init__(self, settings: Optional[GcpVmOffloadSettings] = None):
        cfg = _load_confidential_config()
        if settings is None:
            gcp_cfg = (cfg.get("gcp") or {})
            project_id = (
                gcp_cfg.get("project_id")
                or cfg.get("backend", {}).get("project_id")
                or cfg.get("app", {}).get("backend_project_id")
                or cfg.get("BACKEND_PROJECT_ID")
            )
            zone = gcp_cfg.get("zone", "us-central1-a")
            machine_type = gcp_cfg.get("machine_type", "e2-standard-4")
            disk_size_gb = int(gcp_cfg.get("disk_size_gb", 50))
            image_project = gcp_cfg.get("image_project", "debian-cloud")
            image_family = gcp_cfg.get("image_family", "debian-12")
            service_account_email = gcp_cfg.get("service_account_email")
            results_bucket = (
                gcp_cfg.get("results_bucket")
                or cfg.get("app", {}).get("results_bucket")
                or ""
            )
            timeout_minutes = int(
                (cfg.get("offload") or {}).get("max_minutes")
                or (cfg.get("app") or {}).get("offload_max_minutes")
                or 60
            )
            service_account_file = gcp_cfg.get("service_account_file")
            settings = GcpVmOffloadSettings(
                project_id=project_id,
                zone=zone,
                machine_type=machine_type,
                disk_size_gb=disk_size_gb,
                image_project=image_project,
                image_family=image_family,
                service_account_email=service_account_email,
                results_bucket=results_bucket,
                timeout_minutes=timeout_minutes,
                service_account_file=service_account_file,
            )
        if not settings.project_id:
            raise ValueError("GCP project_id is required in confidential config under 'gcp.project_id' or 'backend.project_id'.")
        if not settings.results_bucket:
            raise ValueError("results_bucket is required in confidential config under 'gcp.results_bucket'.")
        self.settings = settings

        # Best-effort: ensure required services are enabled for this project
        self._ensure_gcp_apis_enabled()

        # Initialize credentials for both compute and storage
        self.credentials = self._init_credentials_with_fallback()
        self.compute = discovery.build("compute", "v1", credentials=self.credentials, cache_discovery=False)
        self.storage_client = storage.Client(project=self.settings.project_id, credentials=self.credentials)

    def _run_gcloud(self, args: list[str]) -> subprocess.CompletedProcess:
        if shutil.which("gcloud") is None:
            raise RuntimeError("Google Cloud SDK (gcloud) is not installed or not on PATH.")
        cmd = ["gcloud", *args, "--quiet"]
        return subprocess.run(cmd, check=True, capture_output=True, text=True)

    def _ensure_gcp_apis_enabled(self) -> None:
        try:
            self._run_gcloud([
                "services", "enable",
                "compute.googleapis.com",
                "storage.googleapis.com",
                "--project", self.settings.project_id,
            ])
        except Exception:
            # Ignore if gcloud is missing or user lacks permission; Compute API calls will fail clearly later.
            pass

    def _maybe_bootstrap_gcloud_adc(self) -> None:
        try:
            self._run_gcloud(["config", "set", "project", self.settings.project_id])
        except Exception:
            return
        try:
            # This may open a browser window for device login on first run.
            self._run_gcloud(["auth", "application-default", "login"])  # --quiet already appended
            # Optionally set quota project for ADC
            self._run_gcloud(["auth", "application-default", "set-quota-project", self.settings.project_id])
        except Exception:
            # If login fails (headless env), fall through to other credential options
            pass

    def _init_credentials_with_fallback(self):
        # 1) Try ADC (preferred, via gcloud ADC)
        try:
            creds, _ = google.auth.default(scopes=SCOPES)
            return creds
        except DefaultCredentialsError:
            # Attempt to bootstrap ADC with gcloud if possible
            self._maybe_bootstrap_gcloud_adc()
            try:
                creds, _ = google.auth.default(scopes=SCOPES)
                return creds
            except DefaultCredentialsError:
                pass

        # 2) Try GOOGLE_APPLICATION_CREDENTIALS env var
        gac_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if gac_path and Path(gac_path).exists():
            return service_account.Credentials.from_service_account_file(gac_path, scopes=SCOPES)

        # 3) Try service_account_file from confidential config
        if self.settings.service_account_file and Path(self.settings.service_account_file).exists():
            return service_account.Credentials.from_service_account_file(self.settings.service_account_file, scopes=SCOPES)

        # 4) Give actionable error
        raise RuntimeError(
            "Google credentials not found. Fix by either:\n"
            "- Run: gcloud auth application-default login\n"
            f"- Or set GOOGLE_APPLICATION_CREDENTIALS to a service account key JSON\n"
            f"- Or set gcp.service_account_file in config_confidential.yaml\n"
            f"Then retry. Project: {self.settings.project_id}\n"
            "Docs: https://cloud.google.com/docs/authentication/external/set-up-adc"
        )

    def offload_and_wait(self, tunable_params: Dict[str, Any]) -> Dict[str, Any]:
        run_id = f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        instance_name = f"chasehound-{run_id}".lower()
        bucket = self.settings.results_bucket
        gcs_prefix = f"runs/{run_id}"

        metadata_items = [
            {"key": "tunable_params", "value": json.dumps(tunable_params)},
            {"key": "results_bucket", "value": bucket},
            {"key": "gcs_prefix", "value": gcs_prefix},
            {"key": "run_id", "value": run_id},
        ]
        startup_script = self._build_startup_script()
        self._create_instance(instance_name, metadata_items, startup_script)

        status_blob_path = f"{gcs_prefix}/status.json"
        deadline = time.time() + self.settings.timeout_minutes * 60
        status = None
        while time.time() < deadline:
            try:
                blob = self.storage_client.bucket(bucket).blob(status_blob_path)
                if blob.exists():
                    data = blob.download_as_text()
                    status = json.loads(data)
                    break
            except Exception:
                pass
            time.sleep(10)

        if status is None:
            raise TimeoutError(
                f"Timed out waiting for offloaded job status at gs://{bucket}/{status_blob_path}"
            )

        try:
            self._delete_instance(instance_name)
        except Exception:
            pass

        return {
            "run_id": run_id,
            "status": status.get("status", "unknown"),
            "result_zip_signed_url": status.get("result_zip_signed_url"),
            "gcs_folder": f"gs://{bucket}/{gcs_prefix}",
        }

    def _create_instance(self, name: str, metadata_items: Dict[str, str], startup_script: str) -> None:
        s = self.settings
        machine_type_url = f"zones/{s.zone}/machineTypes/{s.machine_type}"
        image_response = self.compute.images().getFromFamily(project=s.image_project, family=s.image_family).execute()
        source_disk_image = image_response["selfLink"]

        sa_scopes = [
            "https://www.googleapis.com/auth/devstorage.read_write",
            "https://www.googleapis.com/auth/cloud-platform",
        ]
        service_accounts = [
            {
                "email": s.service_account_email or "default",
                "scopes": sa_scopes,
            }
        ]

        config = {
            "name": name,
            "machineType": machine_type_url,
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": {
                        "sourceImage": source_disk_image,
                        "diskSizeGb": s.disk_size_gb,
                    },
                }
            ],
            "networkInterfaces": [
                {
                    "network": "global/networks/default",
                    "accessConfigs": [
                        {"type": "ONE_TO_ONE_NAT", "name": "External NAT"}
                    ],
                }
            ],
            "serviceAccounts": service_accounts,
            "metadata": {
                "items": [
                    *metadata_items,
                    {"key": "startup-script", "value": startup_script},
                ]
            },
            "labels": {"app": "chasehound"},
        }

        op = self.compute.instances().insert(
            project=s.project_id, zone=s.zone, body=config
        ).execute()
        self._wait_for_zone_operation(op["name"])

    def _delete_instance(self, name: str) -> None:
        s = self.settings
        op = self.compute.instances().delete(project=s.project_id, zone=s.zone, instance=name).execute()
        self._wait_for_zone_operation(op["name"])

    def _wait_for_zone_operation(self, operation: str) -> None:
        s = self.settings
        while True:
            result = self.compute.zoneOperations().get(
                project=s.project_id, zone=s.zone, operation=operation
            ).execute()
            if result.get("status") == "DONE":
                if "error" in result:
                    raise RuntimeError(f"Operation error: {result['error']}")
                return
            time.sleep(3)

    def _build_startup_script(self) -> str:
        script = r"""#!/bin/bash
set -xeuo pipefail

METADATA_HEADER="Metadata-Flavor: Google"
get_meta() {
  curl -sf -H "$METADATA_HEADER" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/$1"
}

RESULTS_BUCKET=$(get_meta results_bucket)
GCS_PREFIX=$(get_meta gcs_prefix)
RUN_ID=$(get_meta run_id)
TUNABLE_PARAMS=$(get_meta tunable_params)

apt-get update -y
apt-get install -y git python3 python3-pip
python3 -m pip install --upgrade pip

mkdir -p /opt
cd /opt
if [ ! -d chaseHound ]; then
  git clone https://github.com/huyuu/chaseHound.git
fi
cd chaseHound

python3 -m pip install -r requirements.txt
python3 -m pip install google-cloud-storage

echo "$TUNABLE_PARAMS" > /opt/chaseHound/params.json

python3 - << 'PYCODE'
import json, sys, os, time
from pathlib import Path

repo_root = Path('/opt/chaseHound')
sys.path.insert(0, str(repo_root / 'src_CD'))
sys.path.insert(0, str(repo_root / 'src_python'))

from backendCDServer import run_chasehound_sync
from google.cloud import storage

params_path = Path('/opt/chaseHound/params.json')
with params_path.open('r', encoding='utf-8') as f:
    tunable_params = json.load(f)

result = run_chasehound_sync(tunable_params)

temp_dir = repo_root / 'temp'
zip_path = repo_root / f"results_{int(time.time())}.zip"
import shutil
if temp_dir.exists():
    shutil.make_archive(zip_path.with_suffix('').as_posix(), 'zip', temp_dir.as_posix())
else:
    with zip_path.open('wb') as f:
        pass

bucket_name = os.environ.get('RESULTS_BUCKET_ENV') or os.popen('curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/results_bucket').read().strip()
prefix = os.environ.get('GCS_PREFIX_ENV') or os.popen('curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs_prefix').read().strip()
client = storage.Client()
bucket = client.bucket(bucket_name)

if temp_dir.exists():
    for root, _, files in os.walk(temp_dir):
        for fname in files:
            local_path = Path(root) / fname
            rel = local_path.relative_to(temp_dir)
            blob = bucket.blob(f"{prefix}/temp/{rel.as_posix()}")
            blob.upload_from_filename(local_path.as_posix())

zip_blob = bucket.blob(f"{prefix}/{zip_path.name}")
zip_blob.upload_from_filename(zip_path.as_posix())

from datetime import timedelta
signed_url = zip_blob.generate_signed_url(expiration=timedelta(days=7), version='v4', method='GET')

status = {
    'status': 'completed',
    'result_zip': f'gs://{bucket_name}/{prefix}/{zip_path.name}',
    'result_zip_signed_url': signed_url,
}

status_path = repo_root / 'status.json'
import json as _json
status_path.write_text(_json.dumps(status), encoding='utf-8')
status_blob = bucket.blob(f"{prefix}/status.json")
status_blob.upload_from_filename(status_path.as_posix())
PYCODE

shutdown -h now || true
"""
        return script 