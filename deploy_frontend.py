import argparse
import sys
from pathlib import Path

from deploy_gcp import deploy_frontend, INFO, SUCCESS, RESET


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy ChaseHound frontend to Google App Engine.")
    parser.add_argument("--frontend-project", default="chasehoundfrontend", help="GCP project ID for frontend")
    parser.add_argument("--backend-project", default="chasehoundbackend", help="GCP project ID for backend")
    parser.add_argument("--region", default="asia-northeast1", help="App Engine region")
    args = parser.parse_args()

    print(f"{INFO} Starting FRONTEND deployment… {RESET}")
    frontend_url = deploy_frontend(args.frontend_project, args.region, args.backend_project)
    print(f"{SUCCESS} Frontend deployed: {frontend_url} {RESET}")


if __name__ == "__main__":
    main() 