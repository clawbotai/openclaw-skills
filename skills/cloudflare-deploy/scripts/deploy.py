from __future__ import annotations

import os
import sys
import tarfile
import json
import logging
from urllib import request, parse, error
from typing import Optional
import argparse

# Set up the logger for the tool
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloudflare-deploy")

API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/"


def get_env_var(key: str) -> Optional[str]:
    """
    Retrieve an environment variable.

    Args:
        key: The environment variable's key to retrieve.

    Returns:
        The value of the environment variable if it exists, else None.
    """
    try:
        return os.environ[key]
    except KeyError:
        logger.error(f"Environment variable '{key}' is not set.")
        return None


def create_tarball(directory_path: str) -> Optional[bytes]:
    """
    Create a tarball from the given directory.

    Args:
        directory_path: The directory path to tar.

    Returns:
        The tarball as bytes.
    """
    try:
        # Create a tarball in memory
        with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as tar:
            tar.add(directory_path, arcname=os.path.basename(directory_path))
        with open(sys.stdout.buffer.fileno(), 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to create tarball: {e}")
        return None


def deploy_to_cloudflare(directory_path: str):
    """
    Deploy a directory to Cloudflare by uploading it as a tarball.

    Args:
        directory_path: The path of the directory to deploy.

    Outputs:
        A JSON object detailing the success or failure of the deployment.
    """
    api_token = get_env_var("CLOUDFLARE_API_TOKEN")
    account_id = get_env_var("CLOUDFLARE_ACCOUNT_ID")

    if not api_token or not account_id:
        sys.exit(1)

    tarball = create_tarball(directory_path)
    if not tarball:
        sys.exit(1)

    url = API_BASE_URL + f"{account_id}/pages/projects/"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/gzip',
    }

    try:
        req = request.Request(url, data=tarball, headers=headers, method='POST')
        with request.urlopen(req) as response:
            result = response.read().decode()
            logger.info("Deployment successful.")
            print(json.dumps({"success": True, "response": json.loads(result)}))
    except error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.reason}")
        print(json.dumps({"success": False, "error": f"HTTP Error: {e.code} - {e.reason}"}))
    except error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        print(json.dumps({"success": False, "error": f"URL Error: {e.reason}"}))
    except Exception as e:
        logger.error(f"General Error: {e}")
        print(json.dumps({"success": False, "error": "General Error: Failed to deploy."}))


def main():
    parser = argparse.ArgumentParser(description='Deploy a directory to Cloudflare Pages.')
    parser.add_argument('directory', type=str, help='The path to the directory to deploy.')
    args = parser.parse_args()

    deploy_to_cloudflare(args.directory)


if __name__ == "__main__":
    main()
