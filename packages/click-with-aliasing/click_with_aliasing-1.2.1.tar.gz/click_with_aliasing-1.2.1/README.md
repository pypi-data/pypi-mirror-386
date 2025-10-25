# Click With Aliasing

![top language](https://img.shields.io/github/languages/top/marcusfrdk/click-with-aliasing)
![code size](https://img.shields.io/github/languages/code-size/marcusfrdk/click-with-aliasing)
![last commit](https://img.shields.io/github/last-commit/marcusfrdk/click-with-aliasing)
![issues](https://img.shields.io/github/issues/marcusfrdk/click-with-aliasing)
![contributors](https://img.shields.io/github/contributors/marcusfrdk/click-with-aliasing)
![PyPI](https://img.shields.io/pypi/v/click-with-aliasing)
![License](https://img.shields.io/github/license/marcusfrdk/click-with-aliasing)
![Downloads](https://static.pepy.tech/badge/click-with-aliasing)
![Monthly Downloads](https://static.pepy.tech/badge/click-with-aliasing/month)

A powerful extension for [Click](https://click.palletsprojects.com/) that adds **command and group aliasing** support with **automatic async function handling** and **advanced parameter validation**.

You can find the project on [PyPi](https://pypi.org/project/click-with-aliasing/).

## Features

- **Command Aliases**: Create multiple names for your commands
- **Group Aliases**: Add aliases to command groups
- **Help Alias (-h)**: Automatic `-h` shorthand for `--help` with conflict detection
- **Enhanced Options & Arguments**: Mutual exclusivity, requirements, and group constraints
- **Validation Rules**: Group-level validation with multiple modes (all_or_none, at_least, at_most, exactly)
- **Automatic Async Support**: Seamlessly handle async functions without extra configuration
- **Drop-in Replacement**: Works exactly like standard Click decorators
- **Type Safe**: Full type hints support with proper IDE integration
- **Help Integration**: Aliases automatically appear in help text

## Installation

```bash
pip install click-with-aliasing
```

**Requirements:** Python 3.10 or newer

## Documentation

- **[Command](docs/COMMAND.md)** - Command decorator with aliasing support
- **[Group](docs/GROUP.md)** - Group decorator for organizing commands
- **[Option](docs/OPTION.md)** - Enhanced options with mutual exclusivity and requirements
- **[Argument](docs/ARGUMENT.md)** - Enhanced arguments with validation constraints
- **[Rule](docs/RULE.md)** - Group-level validation rules for complex parameter logic

> **Note:** Both `-h` and `--help` flags are supported by default. See the [Command](docs/COMMAND.md) and [Group](docs/GROUP.md) documentation for details on how `-h` is intelligently handled when commands use it for other purposes.

## Quick Start

### Basic Command with Aliases

```python
from click_with_aliasing import command

@command(name="deploy", aliases=["d", "dep"])
def deploy():
    """Deploy the application"""
    print("Deploying application...")
```

Now you can run any of these:

```bash
my-cli deploy
my-cli d
my-cli dep
```

### Group with Aliases

```python
from click_with_aliasing import group, command

@group(name="database", aliases=["db"])
def database():
    """Database management commands"""
    pass

@command(name="migrate", aliases=["m"])
def migrate():
    """Run database migrations"""
    print("Running migrations...")

database.add_command(migrate)
```

Usage:

```bash
my-cli database migrate  # Full names
my-cli db m              # Using aliases
my-cli database m        # Mixed usage
```

### Enhanced Options with Validation

```python
from click_with_aliasing import command, option

@command(name="auth")
@option("--username", requires=["password"], mutually_exclusive=["token"])
@option("--password", requires=["username"], mutually_exclusive=["token"])
@option("--token", mutually_exclusive=["username", "password"])
def auth(username, password, token):
    """Authenticate with username/password or token"""
    if token:
        print("Authenticating with token")
    elif username and password:
        print(f"Authenticating as {username}")
```

Usage:

```bash
my-cli auth --token abc123                          # Valid
my-cli auth --username admin --password secret      # Valid
my-cli auth --username admin                        # Error: requires password
my-cli auth --token abc123 --username admin         # Error: mutually exclusive
```

### Validation Rules

```python
from click_with_aliasing import command, option, rule

@command(name="deploy")
@option("--production", is_flag=True)
@option("--staging", is_flag=True)
@option("--development", is_flag=True)
@rule(["production", "staging", "development"], mode="exactly", count=1)
def deploy(production, staging, development):
    """Deploy to exactly one environment"""
    env = "production" if production else "staging" if staging else "development"
    print(f"Deploying to {env}")
```

Usage:

```bash
my-cli deploy --production                          # Valid
my-cli deploy --staging                             # Valid
my-cli deploy --production --staging                # Error: exactly 1 required
my-cli deploy                                       # Error: exactly 1 required
```

## Async Support

The library automatically detects and handles async functions, meaning no extra configuration is needed.

### Async Commands

```python
import asyncio
from click_with_aliasing import command

@command(name="fetch", aliases=["f"])
async def fetch():
    """Fetch data asynchronously"""
    await asyncio.sleep(1)
    print("Data fetched!")
```

### Async Groups

```python
import asyncio
from click_with_aliasing import group, command

@group(name="api", aliases=["a"])
async def api_group():
    """API management commands"""
    await asyncio.sleep(0.1)  # Simulate async setup

@command(name="start", aliases=["s"])
async def start_server():
    """Start the API server"""
    print("Starting server...")

api_group.add_command(start_server)
```

## Key Concepts

### Command & Group Aliases

Add multiple names to commands and groups for convenience:

```python
@command(name="deploy", aliases=["d", "dep"])
@group(name="database", aliases=["db", "d"])
```

### Option Validation

**Mutual Exclusivity**: Only one option from a set can be used

```python
@option("--json", mutually_exclusive=["xml", "yaml"])
```

**Requirements**: Options that must be used together

```python
@option("--username", requires=["password"])
```

**Group Constraints**: Organize options and apply constraints collectively

```python
@option("--json", group="format", group_mutually_exclusive=["output"])
```

### Validation Rules

Apply group-level validation with different modes:

- **all_or_none**: All parameters or none
- **at_least**: Minimum number required
- **at_most**: Maximum number allowed
- **exactly**: Exact number required

```python
@rule(["host", "port", "database"], mode="all_or_none")
@rule(["email", "sms", "slack"], mode="at_least", count=1)
@rule(["json", "xml", "yaml"], mode="at_most", count=1)
@rule(["file1", "file2", "file3"], mode="exactly", count=2)
```

## Migration from Click

Migrating from standard Click is straightforward - just change your imports:

### Before (Standard Click)

```python
import click

@click.group()
def cli():
    pass

@click.command()
@click.option("--name", default="World")
@click.argument("file")
def greet(name, file):
    pass
```

### After (Click with Aliasing)

```python
from click_with_aliasing import group, command, option, argument

@group(aliases=["c"])
def cli():
    pass

@command(name="greet", aliases=["g"])
@option("--name", default="World", mutually_exclusive=["file"])
@argument("file", required=False, mutually_exclusive=["name"])
def greet(name, file):
    pass
```

All standard Click features work exactly the same, with optional enhancements available.

## Help Text Integration

Aliases automatically appear in help text, and both `-h` and `--help` work for displaying help:

```txt
myapp database --help
Usage: myapp database [OPTIONS] COMMAND [ARGS]...

  Database management commands

Options:
  -h, --help  Show this message and exit.

Commands:
  migrate (m, mig)  Run database migrations
  seed (s)          Seed the database
```

The `-h` flag is automatically added unless a command uses it for another purpose (like `--host`), ensuring consistent help access while avoiding conflicts.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our development process, coding standards, and how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built on top of the great [Click](https://click.palletsprojects.com/) library by the Pallets team.
