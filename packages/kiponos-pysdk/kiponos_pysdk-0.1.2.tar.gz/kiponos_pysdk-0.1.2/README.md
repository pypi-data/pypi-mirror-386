# Kiponos Python SDK

The Kiponos Python SDK enables real-time configuration management via WebSocket/STOMP. It connects to the Kiponos server, fetches a configuration tree, and subscribes to updates for dynamic config changes.

## Installation

Install via pip:

```bash
pip install kiponos-pysdk
```

## Prerequisites

- Python 3.12 or higher
- Environment variables: `KIPONOS_ID` and `KIPONOS_ACCESS` (obtain from your Kiponos team account)

## Usage

### Basic Example

```python
from kiponos_pysdk import KiponosClient

# Initialize client
client = KiponosClient(
    server_url="wss://kiponos.io/api/io-kiponos-sdk",
    kiponos="['Kiponos-Server']['3.0']['Dev']['Factory-Settings']"
)

try:
    # Connect and fetch config
    client.connect()
    print(f"Team ID: {client.team_id}")
    print(f"Value: {client.get('tag-test', 'not found')}")

    # Keep program running to receive updates
    input("Press Enter to exit...")
finally:
    client.close()
```

### Interactive Example

Run `example_app.py` for an interactive CLI:

```bash
poetry run python example_app.py
```

Commands:
- `get <key>`: Get value for a key
- `list-keys`: List all config keys
- `dump`: Print the entire config tree
- `exit`: Stop the program

## Configuration

Set environment variables:

```bash
export KIPONOS_ID="your-kiponos-id"
export KIPONOS_ACCESS="your-kiponos-access"
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Support

Contact: [support@kiponos.io](mailto:support@kiponos.io)
Homepage: [https://kiponos.io](https://kiponos.io)
