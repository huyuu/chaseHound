import argparse
from deploy_gcp import deploy_backend, INFO, SUCCESS, RESET


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy ChaseHound backend to Google App Engine.")
    parser.add_argument("--backend-project", default="chasehoundbackend", help="GCP project ID for backend")
    parser.add_argument("--region", default="asia-northeast1", help="App Engine region")
    args = parser.parse_args()

    print(f"{INFO} Starting BACKEND deployment… {RESET}")
    backend_url = deploy_backend(args.backend_project, args.region)
    print(f"{SUCCESS} Backend deployed: {backend_url} {RESET}")


if __name__ == "__main__":
    main() 