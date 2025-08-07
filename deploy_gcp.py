import argparse
import subprocess
import sys
from pathlib import Path

# Ensure src_python is in path to import ChaseHoundBase
ROOT = Path(__file__).resolve().parent
SRC_PYTHON = ROOT / "src_python"
if str(SRC_PYTHON) not in sys.path:
    sys.path.append(str(SRC_PYTHON))

from ChaseHoundBase import ChaseHoundBase as _Base  # type: ignore

GREEN = _Base.green_color_code
RED = _Base.red_color_code
YELLOW = _Base.yellow_color_code
CYAN = "\033[96m"  # ChaseHoundBase has no cyan; define here for INFO
RESET = _Base.reset_color_code

# Preformatted prefixes
INFO = f"{CYAN}[INFO]"
SUCCESS = f"{GREEN}[SUCCESS]"
ERROR = f"{RED}[ERROR]"
WARNING = f"{YELLOW}[WARNING]"

# -----------------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------------

def run_cmd(cmd: str | list[str], error_msg: str) -> None:
    """Run a shell command and exit on failure."""
    printable = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"{INFO} Executing: {printable} {RESET}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{ERROR} {error_msg}\n{result.stderr} {RESET}")
        sys.exit(result.returncode)


# -----------------------------------------------------------------------------
# Deployment steps
# -----------------------------------------------------------------------------

def deploy_backend(project_id: str, region: str) -> str:
    print(f"{INFO} Starting backend deployment… {RESET}")
    run_cmd(["gcloud", "config", "set", "project", project_id], "Failed to set backend project")
    run_cmd([
        "gcloud",
        "services",
        "enable",
        "appengine.googleapis.com",
        "cloudbuild.googleapis.com",
    ], "Failed to enable APIs for backend")
    # Create App Engine application (ignore error if it already exists)
    subprocess.run(["gcloud", "app", "create", f"--region={region}"], capture_output=True)
    print(f"{INFO} App Engine ready for backend {RESET}")
    run_cmd(["gcloud", "app", "deploy", "backend_app.yaml", "--quiet"], "Backend deployment failed")
    backend_url = f"https://{project_id}.appspot.com"
    print(f"{SUCCESS} Backend deployed: {backend_url} {RESET}")
    return backend_url


def update_frontend_yaml(frontend_yaml: Path, backend_project_id: str) -> None:
    content = frontend_yaml.read_text(encoding="utf-8")
    frontend_yaml.write_text(content.replace("BACKEND_PROJECT_ID", backend_project_id), encoding="utf-8")
    print(f"{INFO} Frontend configuration updated with backend project id {RESET}")


def deploy_frontend(project_id: str, region: str, backend_project_id: str) -> str:
    print(f"{INFO} Starting frontend deployment… {RESET}")
    run_cmd(["gcloud", "config", "set", "project", project_id], "Failed to set frontend project")
    run_cmd([
        "gcloud",
        "services",
        "enable",
        "appengine.googleapis.com",
        "cloudbuild.googleapis.com",
    ], "Failed to enable APIs for frontend")
    subprocess.run(["gcloud", "app", "create", f"--region={region}"], capture_output=True)
    print(f"{INFO} App Engine ready for frontend {RESET}")

    frontend_yaml = Path("src_CD/frontend/frontend_app.yaml")
    if not frontend_yaml.exists():
        print(f"{ERROR} {frontend_yaml} not found {RESET}")
        sys.exit(1)
    update_frontend_yaml(frontend_yaml, backend_project_id)

    run_cmd(["gcloud", "app", "deploy", str(frontend_yaml), "--quiet"], "Frontend deployment failed")
    frontend_url = f"https://{project_id}.appspot.com"
    print(f"{SUCCESS} Frontend deployed: {frontend_url} {RESET}")
    return frontend_url


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy ChaseHound backend and frontend to Google App Engine.")
    parser.add_argument("--backend-project", default="chasehoundbackend", help="GCP project ID for backend")
    parser.add_argument("--frontend-project", default="chasehoundfrontend", help="GCP project ID for frontend")
    parser.add_argument("--region", default="asia-northeast1", help="App Engine region")
    args = parser.parse_args()

    print(f"{INFO} Starting ChaseHound deployment process… {RESET}")

    backend_url = deploy_backend(args.backend_project, args.region)
    frontend_url = deploy_frontend(args.frontend_project, args.region, args.backend_project)

    print(f"{SUCCESS} ChaseHound deployment completed successfully! {RESET}")
    print(f"{SUCCESS} Backend URL:  {backend_url} {RESET}")
    print(f"{SUCCESS} Frontend URL: {frontend_url} {RESET}")
    print(f"{INFO} Your ChaseHound application is now live and accessible worldwide! {RESET}")


if __name__ == "__main__":
    main() 