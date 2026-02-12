from __future__ import annotations
import os
import sys
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/"

# Environment variables
API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')


def request_cloudflare_api(endpoint: str, method: str = 'GET', data: Optional[dict] = None) -> Optional[dict]:
    """
    Make a request to the Cloudflare API.

    Args:
        endpoint: The API endpoint to be accessed.
        method: HTTP method to be used for the request.
        data: Data to send with the request (for POST, PUT, etc.).

    Returns:
        The JSON response as a dictionary if successful, or None if there was an error.
    """
    if API_TOKEN is None or ACCOUNT_ID is None:
        logging.error("Environment variables CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set.")
        return None

    url = f"{API_BASE_URL}{ACCOUNT_ID}{endpoint}"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }

    if data:
        data = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.load(response)
            return result
    except urllib.error.HTTPError as e:
        logging.error(f"HTTP error occurred: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        logging.error(f"URL error occurred: {e.reason}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

    return None


def create_project(project_name: str, subdomain: str) -> None:
    """
    Create a new Cloudflare Pages project.

    Args:
        project_name: The name of the project to create.
        subdomain: The subdomain for the project.
    """
    data = {
        'name': project_name,
        'subdomain': subdomain
    }
    result = request_cloudflare_api("/pages/projects", method='POST', data=data)
    if result:
        print(json.dumps(result))
    else:
        logging.error("Failed to create the project.")


def list_projects() -> None:
    """
    List all Cloudflare Pages projects for the account.
    """
    result = request_cloudflare_api("/pages/projects")
    if result:
        print(json.dumps(result))
    else:
        logging.error("Failed to list projects.")


def delete_project(project_id: str) -> None:
    """
    Delete a Cloudflare Pages project.

    Args:
        project_id: The ID of the project to be deleted.
    """
    result = request_cloudflare_api(f"/pages/projects/{project_id}", method='DELETE')
    if result:
        print(json.dumps(result))
    else:
        logging.error("Failed to delete the project.")


def main(args: list[str]) -> None:
    """
    Main entry point for the script, handling command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Manage Cloudflare Projects: create, list, delete.")
    subparsers = parser.add_subparsers(dest='command')

    # Sub-parser for create command
    parser_create = subparsers.add_parser('create', help='Create a new project.')
    parser_create.add_argument('project_name', help='The name of the project to create.')
    parser_create.add_argument('subdomain', help='The subdomain for the project.')

    # Sub-parser for list command
    subparsers.add_parser('list', help='List all projects.')

    # Sub-parser for delete command
    parser_delete = subparsers.add_parser('delete', help='Delete the specified project.')
    parser_delete.add_argument('project_id', help='The ID of the project to delete.')

    parsed_args = parser.parse_args(args)

    if parsed_args.command == 'create':
        create_project(parsed_args.project_name, parsed_args.subdomain)
    elif parsed_args.command == 'list':
        list_projects()
    elif parsed_args.command == 'delete':
        delete_project(parsed_args.project_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main(sys.argv[1:])
