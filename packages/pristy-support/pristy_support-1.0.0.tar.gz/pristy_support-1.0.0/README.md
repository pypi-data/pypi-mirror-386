# Pristy Support

Audit and support tools for Pristy ECM installations.

## Overview

Pristy Support is a command-line tool designed to help support teams diagnose and audit Pristy installations. It performs comprehensive checks on system resources, services, logs, database statistics, and configuration files, generating detailed reports in multiple formats.

## Features

### System Checks
- ✅ Systemd services status (enabled/active)
- ✅ Docker containers health
- ✅ Memory configuration and limits validation
- ✅ Swap presence and size
- ✅ Firewall status detection
- ✅ Disk space monitoring
- ✅ System load analysis

### Logs Analysis
- 🔍 Journalctl log analysis for all Pristy services
- 🔍 Error and warning detection
- 🔍 Log severity aggregation
- 🔍 Common error pattern extraction

### Database Statistics
- 📊 Node, property, and aspect counts
- 📊 User and group statistics
- 📊 Content statistics
- 📊 Database and table sizes
- 📊 Useful ratios (properties/node, aspects/node)

### Configuration Review
- 📄 Alfresco global.properties analysis
- 📄 Pristy Vue.js application configurations
- 📄 Key parameter extraction
- 📄 Configuration issue detection

### Export Formats
- 📝 **Markdown**: Clean text reports
- 🌐 **HTML**: Styled, navigable reports
- 📦 **ZIP**: Complete archives with all data and reports

## Installation

### From Source

* with uv

```bash
cd pristy-support
uv venv
uv pip install .
```

* without uv


```bash
cd pristy-support

python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### For Development

```bash
cd pristy-support
pip install -e .
```

### For Client Deployment

Once published to a package index:

```bash
pip install pristy-support
```

## Configuration

Pristy Support can be customized via YAML configuration files. The tool looks for configuration in these locations (in order of priority):
1. Custom path specified with `--config` option
2. `./pristy-support.yml` (current directory)
3. `./.pristy-support.yml` (current directory, hidden)
4. `~/.pristy-support.yml` (user home directory)
5. `~/.config/pristy-support/config.yml` (XDG config directory)
6. `/etc/pristy/pristy-support.yml` (system-wide configuration)

### Generate Default Configuration

Create a configuration file with all default values:

```bash
pristy-support init-config
```

This creates `pristy-support.yml` in the current directory. You can specify a custom output path:

```bash
pristy-support init-config --output /path/to/config.yml
```

### Configuration Options

The configuration file allows you to customize:
- **System**: Services to check, memory thresholds, disk space thresholds
- **Docker**: Container name patterns to monitor
- **Logs**: Services to analyze, time periods, severity keywords, max samples per severity
- **Database**: PostgreSQL connection parameters
- **Config Paths**: Paths for Alfresco and Pristy application configurations
- **Audit**: Default export formats and output directory

Example configuration snippet:

```yaml
system:
  services:
    - postgres
    - kafka
    - alfresco
  memory:
    min_ram_gb: 8
    recommended_ram_gb: 12
    min_swap_gb: 2
  disk_thresholds:
    /: 10
    /var/lib/docker: 30

logs:
  services:
    - alfresco
    - solr6
  default_since: 7d
  max_samples_per_severity: 10
  severity_keywords:
    critical: [CRITICAL, FATAL]
    error: [ERROR]
    warning: [WARN, WARNING]
```

### Using Custom Configuration

```bash
pristy-support --config /path/to/config.yml audit
```

## Usage

### Full Audit

Run a complete audit of your Pristy installation:

```bash
pristy-support audit
```

This will generate reports in the current directory in all formats (Markdown, HTML, and ZIP).

#### Options

```bash
pristy-support audit --output-dir /path/to/output --formats md,html,zip --since 30d
```

- `--output-dir`, `-o`: Output directory for reports (default: current directory)
- `--formats`, `-f`: Export formats, comma-separated (default: `md,html,zip`)
- `--since`, `-s`: Time period for log analysis (default: `7d`)

Examples:
- `--since 24h`: Last 24 hours
- `--since 7d`: Last 7 days (default)
- `--since 30d`: Last 30 days

### Individual Checks

Run specific checks independently:

#### System Checks Only

```bash
pristy-support system-check
```

#### Logs Analysis Only

```bash
pristy-support logs-check --since 7d
```

#### Database Statistics Only

```bash
pristy-support database-check
```

#### Configuration Review Only

```bash
pristy-support config-check
```

### Version

```bash
pristy-support --version
```

### Help

```bash
pristy-support --help
pristy-support audit --help
```

### Debug Mode

Enable debug mode to see all commands executed by the tool:

```bash
pristy-support --debug audit
```

Debug mode displays:
- All system commands before execution (systemctl, journalctl, docker, etc.)
- Command results (success/failure with exit codes)
- Docker exec operations with container names
- File read/write operations

Example output:
```
DEBUG [pristy_support] 🔧 Checking systemctl availability
DEBUG [pristy_support]    $ systemctl --version
DEBUG [pristy_support]    ✓ Command succeeded (exit code: 0)
DEBUG [pristy_support] 🔧 Listing Docker containers
DEBUG [pristy_support]    $ docker ps --format {{.ID}}|{{.Names}}|{{.Status}}|{{.Image}} -a
DEBUG [pristy_support]    ✓ Command succeeded (exit code: 0)
DEBUG [pristy_support] 🐳 Executing in container 'postgres':
DEBUG [pristy_support]    $ psql -U alfresco -d alfresco -t -A -c SELECT COUNT(*) FROM alf_node;
```

This is useful for:
- Troubleshooting issues
- Understanding what the tool is doing
- Debugging permission problems
- Support and diagnostics

## Requirements

### System Requirements

- Python 3.9 or higher
- Linux operating system (systemd-based)
- Docker (for container checks and PostgreSQL access)

### Permissions

The tool automatically detects available permissions and adapts its checks accordingly:

- **Root/sudo**: Full access to all checks
- **Docker group**: Access to Docker commands
- **Standard user**: Limited checks (may miss some system information)

For best results, run with sudo or as root:

```bash
sudo pristy-support audit
```

### Pristy Installation

The tool expects a standard Pristy installation with:

- Systemd services for Pristy components
- Docker containers running Pristy services
- PostgreSQL database in a Docker container named `postgres`
- Configuration files in standard locations:
  - `/opt/alfresco/tomcat/shared/classes/alfresco-global.properties`
  - `/opt/pristy-*/public/env-config.json`

## Architecture

### Project Structure

```
pristy-support/
├── pristy_support/
│   ├── __init__.py
│   ├── __main__.py          # Entry point for python -m pristy_support
│   ├── cli.py               # CLI interface (Click)
│   ├── modules/             # Audit modules
│   │   ├── system.py        # System checks
│   │   ├── logs.py          # Log analysis
│   │   ├── database.py      # Database statistics
│   │   └── config.py        # Configuration review
│   ├── exporters/           # Report exporters
│   │   ├── markdown.py      # Markdown exporter
│   │   ├── html.py          # HTML exporter
│   │   └── zip_exporter.py  # ZIP archive exporter
│   ├── utils/               # Utilities
│   │   ├── permissions.py   # Permission detection
│   │   ├── docker_utils.py  # Docker utilities
│   │   └── logger.py        # Debug logging
│   └── templates/           # HTML templates
│       └── report.html.j2
├── tests/                   # Unit tests
├── setup.py                 # Package setup
├── pyproject.toml           # Modern packaging metadata
├── requirements.txt         # Dependencies
├── README.md                # This file
└── LICENSE                  # AGPL-3.0 license

```

### Modules

#### System Module (`system.py`)
Checks system resources and services:
- Systemd service status
- Docker container health
- Memory and swap configuration
- Disk space availability
- System load

#### Logs Module (`logs.py`)
Analyzes system logs via journalctl:
- Searches for ERROR, WARN, FATAL keywords
- Aggregates by service and severity
- Extracts common error patterns

#### Database Module (`database.py`)
Collects PostgreSQL statistics:
- Executes queries via `docker exec` on postgres container
- Counts nodes, properties, aspects, users, groups
- Calculates useful ratios
- Reports database and table sizes

#### Config Module (`config.py`)
Reviews configuration files:
- Parses alfresco-global.properties
- Reads Vue.js env-config.json files
- Validates key parameters
- Detects configuration issues

### Exporters

#### Markdown Exporter
Generates clean, readable text reports with tables.

#### HTML Exporter
Creates styled HTML reports with:
- Responsive layout
- Color-coded status badges
- Sortable tables
- Metrics cards

#### ZIP Exporter
Bundles all reports and raw data:
- Markdown report
- HTML report
- Raw JSON data
- Individual module data files

## Development

### Setup Development Environment

```bash
git clone https://gitlab.com/pristy-oss/pristy-support.git
cd pristy-support
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black pristy_support/
```

### Type Checking

```bash
mypy pristy_support/
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using conventional commits
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 100)
- Add type hints where possible
- Write docstrings for all functions and classes
- All code comments in English

### Commit Messages

Use conventional commits format:
- `feat(module): add new feature`
- `fix(logs): correct error detection`
- `docs(readme): update installation instructions`
- `refactor(system): improve memory check logic`

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later).

See [LICENSE](LICENSE) file for details.

## Authors

- **JECI SARL** - [https://www.jeci.fr](https://jeci.fr/en/)
- **PRISTY** - [https://www.pristy.fr](https://pristy.fr/en)

## Support

For issues, questions, or contributions:
- GitHub Issues: [https://gitlab.com/pristy-oss/pristy-support/-/issues)

## Changelog

### Version 1.0.0 (2025-01-XX)

Initial release:
- System checks (services, containers, memory, disk, load)
- Logs analysis with error detection
- Database statistics collection
- Configuration review
- Multiple export formats (Markdown, HTML, ZIP)
- Automatic permission detection
- CLI interface with Click
- Debug mode with command tracing
- YAML configuration system with customizable parameters
- `init-config` command to generate default configuration

## Roadmap

Future enhancements:
- [ ] Interactive mode for detailed investigation
- [ ] Automated issue remediation suggestions
- [ ] Integration with monitoring systems (Prometheus, Grafana)
- [ ] Performance benchmarking
- [ ] Historical trend analysis
- [ ] Multi-server support for clustered installations
- [ ] Email report delivery
- [ ] Scheduled audit execution