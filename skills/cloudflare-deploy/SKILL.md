---
name: cloudflare-deploy
description: Deploy static websites and web apps to Cloudflare Pages using Python's standard library. Includes project management, deployment operations, rollback capabilities, and domain management.
---

## Introduction

The `cloudflare-deploy` skill facilitates deployment to Cloudflare Pages using the standard Python library. This skill allows users to manage projects, create new deployments, check the status, and perform rollbacks—all through Cloudflare's REST API.

## Features
- **Deploy directories to Cloudflare Pages**: Upload content as a tarball to deploy.
- **Project Management**: Create, list, and delete Cloudflare projects effortlessly.
- **Deployment Status and Logs**: Check ongoing deployment status and retrieve logs.
- **Rollback Functionality**: Revert to previous successful deployments if needed.
- **Domain and Environment Management**: Manage custom domains and environment variables for more personalized web app configurations.

## Prerequisites
- Python 3.9+
- Ensure the environment variables `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are set for authentication with Cloudflare's API.

## Usage

### Deploying a Directory
Run `deploy.py` with the path to your deployment directory:
```
python deploy.py /path/to/your/directory
```

### Managing Projects
- **Create a Project**: Run `projects.py create` with required project details.
- **List Projects**: Run `projects.py list` to see all existing projects.
- **Delete a Project**: Run `projects.py delete [project_id]`.

### Checking Deployment Status
Run `status.py` and pass the deployment ID:
```
python status.py status [deployment_id]
```

### Rolling Back a Deployment
Use `status.py rollback` to revert:
```
python status.py rollback [deployment_id]
```

### Debugging and Logs
All scripts will output structured JSON to facilitate integration with logging systems or onward processing.

## Security Notes
- Do not expose your `CLOUDFLARE_API_TOKEN` in logs or error messages.
- Ensure environment variables are secured and not accessible to unauthorized systems.

## Conclusion
The `cloudflare-deploy` provides a convenient interface to manage deployments on Cloudflare, leveraging the power of Python's standard library for minimalistic and efficient operations.