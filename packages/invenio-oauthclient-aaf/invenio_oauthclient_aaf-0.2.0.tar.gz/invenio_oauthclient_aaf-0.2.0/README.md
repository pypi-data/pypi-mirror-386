# Invenio-OAuthClient-AAF

AAF (Australian Access Federation) OAuth integration for InvenioRDM using OpenID Connect.

## Features

- OpenID Connect integration with AAF
- Support for both production and sandbox/test environments
- Automatic user confirmation for trusted identity provider
- Comprehensive test coverage
- Easy configuration

## Installation

### From PyPI

```bash
pip install invenio-oauthclient-aaf
```

### From source

```bash
git clone https://github.com/aus-plant-phenomics-network/invenio-oauthclient-aaf.git
cd invenio-oauthclient-aaf
pip install -e .
```

### For development

```bash
# Install all development dependencies (recommended)
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"

# Quick setup with just
just setup
```

## Configuration

### 1. Register your application with AAF

Visit the AAF Federation Manager and register your InvenioRDM instance. You'll need:

- Client ID
- Client Secret
- Redirect URI: `https://your-domain.com/oauth/authorized/aaf/`

### 2. Configure InvenioRDM

#### Basic Configuration

Add the following to your `invenio.cfg`:

```python
from invenio_oauthclient_aaf import REMOTE_APP

# Add AAF to remote apps
OAUTHCLIENT_REMOTE_APPS = {
    "aaf": REMOTE_APP,
}

# Set your AAF credentials
AAF_APP_CREDENTIALS = {
    "consumer_key": "your-aaf-client-id",
    "consumer_secret": "your-aaf-client-secret",
}
```

#### Advanced Configuration with Helper Class

For more control, use the `AAFSettingsHelper`:

```python
from invenio_oauthclient_aaf import AAFSettingsHelper

# Create a custom AAF configuration
aaf_helper = AAFSettingsHelper(
    title="My Institution",
    description="Login with My Institution AAF",
    base_url="https://central.aaf.edu.au",
    app_key="AAF_APP_CREDENTIALS",
)

OAUTHCLIENT_REMOTE_APPS = {
    "aaf": aaf_helper.remote_app,
}

AAF_APP_CREDENTIALS = {
    "consumer_key": "your-aaf-client-id",
    "consumer_secret": "your-aaf-client-secret",
}
```

### 3. (Optional) Use sandbox environment

For testing with AAF's sandbox environment:

```python
from invenio_oauthclient_aaf import REMOTE_SANDBOX_APP

OAUTHCLIENT_REMOTE_APPS = {
    "aaf": REMOTE_SANDBOX_APP,
}
```

Or with the helper:

```python
from invenio_oauthclient_aaf import AAFSettingsHelper

aaf_sandbox = AAFSettingsHelper(
    title="AAF Sandbox",
    description="AAF Test Environment",
    base_url="https://central.test.aaf.edu.au",
)

OAUTHCLIENT_REMOTE_APPS = {
    "aaf": aaf_sandbox.remote_app,
}
```

### 4. (Optional) Disable local login

If you want to use AAF exclusively:

```python
ACCOUNTS_LOCAL_LOGIN_ENABLED = False
SECURITY_REGISTERABLE = False
SECURITY_RECOVERABLE = False
SECURITY_CHANGEABLE = False
```

### 5. (Optional) Enable auto-redirect

Automatically redirect users to AAF login:

```python
from invenio_oauthclient.views.client import auto_redirect_login

ACCOUNTS_LOGIN_VIEW_FUNCTION = auto_redirect_login
OAUTHCLIENT_AUTO_REDIRECT_TO_EXTERNAL_LOGIN = True
```

### 6. Restart your services

```bash
invenio-cli services stop
invenio-cli services start
```

## Configuration Options

You can customize the AAF integration using the `AAFSettingsHelper`:

### Customizing Signup Options

```python
from invenio_oauthclient_aaf import AAFSettingsHelper

aaf_helper = AAFSettingsHelper(
    title="AAF",
    description="Australian Access Federation",
)

# Get the remote app and customize it
aaf_remote = aaf_helper.remote_app

# Customize signup options
aaf_remote["signup_options"] = {
    "auto_confirm": True,      # Auto-confirm user emails
    "send_register_msg": False, # Don't send registration emails
}

OAUTHCLIENT_REMOTE_APPS = {
    "aaf": aaf_remote,
}
```

### Custom Handler

If you need custom user information handling:

```python
from invenio_oauthclient_aaf import AAFSettingsHelper

class CustomAAFHelper(AAFSettingsHelper):
    """Custom AAF helper with modified handlers."""

    def get_handlers(self):
        """Override to use custom handlers."""
        handlers = super().get_handlers()
        handlers["signup_handler"]["info"] = "myapp.handlers:custom_account_info"
        return handlers

aaf_helper = CustomAAFHelper()

OAUTHCLIENT_REMOTE_APPS = {
    "aaf": aaf_helper.remote_app,
}
```

### Additional Request Parameters

```python
aaf_helper = AAFSettingsHelper(
    title="AAF",
    description="Australian Access Federation",
    request_token_params={
        "scope": "openid profile email eduPersonAffiliation",
        "prompt": "login",  # Force re-authentication
    },
)
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started quickly
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Detailed usage scenarios
- **[Semantic Release Guide](docs/SEMANTIC_RELEASE.md)** - Automated releases with semantic-release
- **[Publishing Guide](PUBLISHING.md)** - Manual publishing process

## Development

### Setup

```bash
# One-command setup (installs deps + pre-commit hooks)
just setup

# Or manually:
uv pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type commit-msg
```

### Running tests

```bash
# Run tests (choose your preferred tool)
uv run pytest       # Direct
just test          # just

# Run tests with coverage
just test-cov      # just

# View coverage report
open htmlcov/index.html
```

### Code Quality

This project uses pre-commit hooks to ensure code quality:

```bash
# Hooks run automatically on commit
git commit -m "feat: add new feature"

# Or run manually on all files
just pre-commit-all

# Update hooks to latest versions
just update-hooks
```

**What runs on each commit:**

- ✅ Trailing whitespace removal
- ✅ End-of-file fixer
- ✅ YAML/TOML validation
- ✅ Ruff linting (with auto-fix)
- ✅ Ruff formatting
- ✅ Conventional commit message validation
- ✅ pyproject.toml validation

### Task Runner

This project uses **`just`** - a modern task runner with simple syntax:

```bash
just            # List all commands
just test       # Run tests
just build      # Build package
```

Install: `brew install just` or see [justfile](justfile) for more options

### Project structure

```
invenio-oauthclient-aaf/
├── invenio_oauthclient_aaf/    # Main package
│   ├── __init__.py              # Package initialization
│   ├── handlers.py              # OAuth handlers
│   └── remote.py                # Remote app configuration
├── tests/                       # Test files
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_handlers.py         # Handler tests
│   └── test_remote.py           # Remote configuration tests
├── docs/                        # Documentation
│   ├── QUICKSTART.md            # Quick start guide
│   ├── README.md                # Documentation index
│   ├── USAGE_EXAMPLES.md        # Usage examples
│   └── SEMANTIC_RELEASE.md      # Semantic release guide
├── scripts/                     # Utility scripts
│   ├── setup_dev.sh             # Development setup script
├── .github/                     # GitHub configuration
│   ├── workflows/               # CI/CD workflows
├── CHANGELOG.md                 # Version changelog
├── CONTRIBUTING.md              # Contribution guidelines
├── PUBLISHING.md                # Publishing guide
├── README.md                    # Main project documentation
├── RELEASE.md                   # Release guide
├── setup.py                     # Package setup configuration
├── pyproject.toml               # Modern Python project configuration
├── justfile                     # Command runner
├── pytest.ini                   # Pytest configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
└── uv.lock                      # UV package lock file
```

## User Attribute Mapping

AAF provides the following user attributes which are mapped to InvenioRDM:

| AAF Attribute        | InvenioRDM Field         | Description                           |
| -------------------- | ------------------------ | ------------------------------------- |
| `sub`                | `external_id`            | Unique user identifier                |
| `email`              | `user.email`             | User email address                    |
| `name`               | `user.profile.full_name` | Full name                             |
| `preferred_username` | `user.profile.username`  | Username (falls back to email prefix) |

## Troubleshooting

### Check logs

View AAF authentication logs:

```bash
docker-compose logs -f web-ui | grep "AAF:"
```

### Enable debug logging

Add to `invenio.cfg`:

```python
import logging
LOGGING_CONSOLE_LEVEL = logging.DEBUG
```

### Common issues

1. **"No access token received"**: Check your AAF client credentials
2. **"AAF did not provide user email"**: Ensure your AAF app requests `email` scope
3. **"ImportError"**: Make sure the package is installed in your virtualenv

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`just test`, `just lint`)
5. Commit your changes using conventional commits:

   ```bash
   # Use interactive commit helper
   just commit

   # Or manually with conventional format
   git commit -m "feat: add amazing feature"
   ```

6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features (triggers minor version bump)
- `fix:` - Bug fixes (triggers patch version bump)
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Code style/formatting changes
- `chore:` - Maintenance tasks

See [Semantic Release Guide](docs/SEMANTIC_RELEASE.md) for detailed information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Links

- [AAF Documentation](https://aaf.edu.au/)
- [AAF OpenID Connect Tutorials](https://tutorials.aaf.edu.au/openid-connect-series/01-overview)
- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [Invenio-OAuthClient Documentation](https://invenio-oauthclient.readthedocs.io/)

## Support

For issues related to this package, please open an issue on GitHub.

For AAF-specific issues, contact AAF support at support@aaf.edu.au.

For InvenioRDM issues, visit the [InvenioRDM](https://github.com/inveniosoftware/invenio-app-rdm).
