# Managing Environment Variables for the `cloudflare-deploy` Skill

Environment variables are essential for securely configuring sensitive information such as API tokens and account identifiers in a software application. For the `cloudflare-deploy` skill, we use environment variables to manage authentication credentials required for interacting with Cloudflare's API.

## Required Environment Variables

To utilize the `cloudflare-deploy` skill effectively, the following environment variables must be set:

- `CLOUDFLARE_API_TOKEN`: This is a token used to authenticate API requests authorized with your Cloudflare account. You can retrieve or create this token via the Cloudflare dashboard.
- `CLOUDFLARE_ACCOUNT_ID`: This is a unique identifier for your Cloudflare account. You can find this on your Cloudflare dashboard, typically under your account settings or profile information.

## Setting Environment Variables

Environment variables can be set differently depending on your operating system and shell. Below are examples for common systems.

### macOS/Linux

For temporary session-level environment variables, you can set them in the terminal:
```sh
export CLOUDFLARE_API_TOKEN='your_api_token'
export CLOUDFLARE_ACCOUNT_ID='your_account_id'
```

To make these changes persistent across sessions, you should add them to your shell's configuration file, such as `~/.bashrc`, `~/.bash_profile`, or `~/.zshrc`:
```sh
echo "export CLOUDFLARE_API_TOKEN='your_api_token'" >> ~/.bashrc
echo "export CLOUDFLARE_ACCOUNT_ID='your_account_id'" >> ~/.bashrc
```
After modifying these files, apply the changes with:
```sh
source ~/.bashrc
```

### Windows

You can set environment variables in the current session using Command Prompt:
```cmd
set CLOUDFLARE_API_TOKEN=your_api_token
set CLOUDFLARE_ACCOUNT_ID=your_account_id
```

For persistent environment variables, use the `setx` command:
```cmd
setx CLOUDFLARE_API_TOKEN "your_api_token"
setx CLOUDFLARE_ACCOUNT_ID "your_account_id"
```
Note: After running `setx`, open a new command prompt window to access the updated environment variables.

### Best Practices

- **Security**: Never hard-code API tokens or sensitive information directly into your scripts. Utilize environment variables to enhance security.
- **Version Control**: Exclude files containing sensitive environment variable settings (like `.bashrc` or `.env` files) from version control systems (e.g., by adding them to `.gitignore`).

## Using Environment Variables in Python

The Python Standard Library provides the `os` module, which can be used to access environment variables within your code. Here's how you can retrieve the necessary variables in a Python script:

```python
import os

api_token = os.getenv('CLOUDFLARE_API_TOKEN')
account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')

if not api_token or not account_id:
    raise RuntimeError('Missing Cloudflare API credentials. Please set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID environment variables.')
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Found**:
   - Ensure that your terminal or command prompt has the correct environment set. You may need to restart the terminal or source your configuration files.

2. **Incorrect Token/ID**:
   - Double-check that the `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` values are correct and up-to-date.

3. **Permission Issues**:
   - The API token used must have appropriate permissions for deployment and management actions you intend to perform.

## Conclusion

Proper management of environment variables is crucial for maintaining security and functionality within the `cloudflare-deploy` skill. By following the guidelines and examples provided, you ensure a more secure and efficient deployment process to Cloudflare Pages.

For more detailed information on how to create and manage API tokens or account settings, consult the official Cloudflare documentation or support.