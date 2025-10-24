# SF Gear (sfgear)

A Python library for Salesforce CLI integration. SF Gear provides convenient wrappers around Salesforce CLI commands to simplify Salesforce development workflows.

## Features

- **CLI Module**: Wrapper around Salesforce CLI commands for data operations and org management
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Zero dependencies**: Uses only Python standard library

## Installation

```bash
pip install sf-gear
```

## Quick Start

```python
from sfgear.cli import data, org

# Query data using SOQL
result = data.query("org-alias", "SELECT Id, Name FROM Account LIMIT 10")

# Get a specific record
record = data.get_record("org-alias", "Account", record_id="001000000000000")

# Get org information
org_info = org.display("org-alias")
```

## Requirements

- Python 3.10+
- Salesforce CLI

### Installing Salesforce CLI

**macOS/Linux:**
```bash
npm install -g @salesforce/cli
```

**Windows:**
```bash
npm install -g @salesforce/cli
```

**Alternative (all platforms):**
Download from [https://developer.salesforce.com/tools/sfcli](https://developer.salesforce.com/tools/sfcli)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
