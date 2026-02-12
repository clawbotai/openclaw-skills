# Cloudflare Pages API Documentation

This document provides comprehensive details on using the Cloudflare Pages API for deploying static websites and web applications. It is designed to help developers integrate deployment functionality into their scripts using Python's standard library.

## Authentication

Cloudflare Pages API requires authentication via the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`, which must be set as environment variables in your script. These are used for all interactions with the API.

- **CLOUDFLARE_API_TOKEN**: Token for authenticating API requests.
- **CLOUDFLARE_ACCOUNT_ID**: Identifier for your Cloudflare account.

## Base URL

All API requests should be made to the following base URL:

```
https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects
```

## Projects Endpoint

### Create a New Project
To create a new project, send a POST request to the projects endpoint.

**Endpoint:**
```
POST /accounts/{account_id}/pages/projects
```

**Headers:**
- `Authorization: Bearer {CLOUDFLARE_API_TOKEN}`
- `Content-Type: application/json`

**Body:**
```json
{
  "name": "project_name",
  "source": {
    "type": "local",
    "config": {
      "contentDirectory": "dist"
    }
  }
}
```

**Example:**

Using Python's `urllib` library, the following example demonstrates how to create a project:

```python
import os
from urllib.request import Request, urlopen
import json

api_token = os.getenv('CLOUDFLARE_API_TOKEN')
account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')

project_url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects'
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

project_data = json.dumps({
    "name": "my-new-project",
    "source": {
        "type": "local",
        "config": {
            "contentDirectory": "dist"
        }
    }
}).encode('utf-8')

request = Request(project_url, data=project_data, headers=headers, method='POST')
with urlopen(request) as response:
    print(json.load(response))
```

### List Projects
List all projects associated with the account.

**Endpoint:**
```
GET /accounts/{account_id}/pages/projects
```

**Headers:**
- `Authorization: Bearer {CLOUDFLARE_API_TOKEN}`

**Example:**

```python
request = Request(project_url, headers=headers, method='GET')
with urlopen(request) as response:
    projects = json.load(response)
    print(projects)
```

### Delete a Project
Delete an existing project by its name.

**Endpoint:**
```
DELETE /accounts/{account_id}/pages/projects/{project_name}
```

**Headers:**
- `Authorization: Bearer {CLOUDFLARE_API_TOKEN}`

## Deployments Endpoint

### Create a Deployment
Deploy a directory as a tarball to Cloudflare Pages.

**Endpoint:**
```
POST /accounts/{account_id}/pages/projects/{project_name}/deployments
```

**Body:**
- You upload the tarball file of the directory you wish to deploy.

### List Deployments
Instead of the JSON structure, ensure it's accurate per user's system.

**Endpoint:**
```
GET /accounts/{account_id}/pages/projects/{project_name}/deployments
```

**Example:**

```python
deployment_url = project_url + '/my-new-project/deployments'
request = Request(deployment_url, headers=headers, method='GET')
with urlopen(request) as response:
    deployments = json.load(response)
    print(deployments)
```

## Custom Domain Management

Adding a custom domain to a project allows you to serve your application from your preferred URL.

### Add Domain

**Endpoint:**
```
POST /accounts/{account_id}/pages/projects/{project_name}/domains
```

**Body:**
```json
{
  "domain": "example.com"
}
```

**Example:**

```python
add_domain_url = deployment_url + '/domains'
domain_data = json.dumps({"domain": "example.com"}).encode('utf-8')

request = Request(add_domain_url, data=domain_data, headers=headers, method='POST')
with urlopen(request) as response:
    print(json.load(response))
```

## Rollback a Deployment

This allows you to rollback the project to a previous deployment.

### Rollback Endpoint
**Endpoint:**
```
POST /accounts/{account_id}/pages/projects/{project_name}/deployments/{deployment_id}/rollback
```

**Example:**

```python
rollback_url = f'{deployment_url}/{deployment_id}/rollback'
request = Request(rollback_url, headers=headers, method='POST')
with urlopen(request) as response:
    rollback_status = json.load(response)
    print(rollback_status)
```

## Environment Variables

Environment variables can be set for projects to customize behavior across deployments.

### Configure Environment Variables
**Endpoint:**
```
PUT /accounts/{account_id}/pages/projects/{project_name}/environment_vars
```

**Body:**
```json
{
  "envName": {
    "value": "envValue",
    "type": "plain"
  }
}
```

By following the examples and standards outlined in this document, users can effectively manage their deployment processes on Cloudflare Pages using Python's standard library.