from __future__ import annotations
import os
import json
import urllib.request
import urllib.error
import sys
import logging
from typing import Optional
import argparse

# Setting up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.cloudflare.com/client/v4"


def get_auth_headers() -> dict[str, str]:
    """
    Retrieve authentication headers required for Cloudflare API requests.

    Returns:
        dict[str, str]: Dictionary containing authorization headers.
    Throws:
        EnvironmentError: If necessary environment variables are not set.
    """
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")

    if not api_token or not account_id:
        raise EnvironmentError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set as environment variables."
        )

    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }


def check_deployment_status(deployment_id: str) -> None:
    """
    Check the status of a specific deployment by its ID and output JSON with the status information.

    Args:
        deployment_id (str): The ID of the deployment to check.
    """
    url = f"{API_BASE_URL}/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/pages/deployments/{deployment_id}"

    try:
        req = urllib.request.Request(url, headers=get_auth_headers())
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            print(json.dumps(data, indent=2))  # Returns formatted JSON to stdout
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error occurred: {e.reason}")
        print(json.dumps({"error": e.reason}, indent=2))
    except urllib.error.URLError as e:
        logger.error(f"URL error occurred: {e.reason}")
        print(json.dumps({"error": e.reason}, indent=2))
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        print(json.dumps({"error": str(e)}, indent=2))


def rollback_deployment(deployment_id: str) -> None:
    """
    Rollback a deployment given its ID.

    Args:
        deployment_id (str): The ID of the deployment to rollback.
    """
    url = f"{API_BASE_URL}/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/pages/deployments/{deployment_id}/rollback"

    try:
        req = urllib.request.Request(url, headers=get_auth_headers(), method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            print(json.dumps(data, indent=2))  # Returns formatted JSON to stdout
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error occurred: {e.reason}")
        print(json.dumps({"error": e.reason}, indent=2))
    except urllib.error.URLError as e:
        logger.error(f"URL error occurred: {e.reason}")
        print(json.dumps({"error": e.reason}, indent=2))
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        print(json.dumps({"error": str(e)}, indent=2))


def main() -> None:
    """
    Main function to handle command-line arguments and trigger the appropriate functions.
    """
    parser = argparse.ArgumentParser(description="Cloudflare Pages Deployment Status and Rollback")
    subparsers = parser.add_subparsers(dest="command")
    
    # Sub-parser for checking status
    status_parser = subparsers.add_parser("status", help="Check deployment status")
    status_parser.add_argument("deployment_id", type=str, help="Deployment ID to check status for")

    # Sub-parser for rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback a deployment")
    rollback_parser.add_argument("deployment_id", type=str, help="Deployment ID to be rolled back")

    args = parser.parse_args()

    if args.command == "status":
        check_deployment_status(args.deployment_id)
    elif args.command == "rollback":
        rollback_deployment(args.deployment_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
