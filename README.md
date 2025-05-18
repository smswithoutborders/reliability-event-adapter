# Reliability Event Adapter

This adapter provides a pluggable implementation for testing the reliability of gateway-clients. It is designed to work with [RelaySMS Publisher](https://github.com/smswithoutborders/RelaySMS-Publisher).

## Requirements

- **Python**: Version >=
  [3.8.10](https://www.python.org/downloads/release/python-3810/)
- **Python Virtual Environments**:
  [Documentation](https://docs.python.org/3/tutorial/venv.html)

## Dependencies

### On Ubuntu

Install the necessary system packages:

```bash
sudo apt install build-essential python3-dev
```

## Installation

1. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**

   ```bash
   . venv/bin/activate
   ```

3. **Install the required Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Configure the database credentials in a `credentials.json` file:
2. Set the path to your credentials file in `config.ini`:

```ini
[credentials]
path=./credentials.json
```

**Sample `credentials.json` for MySQL:**

```json
{
  "engine": "mysql",
  "mysql": {
    "host": "localhost",
    "user": "username",
    "password": "password",
    "database": "reliability_test"
  }
}
```

**Sample `credentials.json` for SQLite:**

```json
{
  "engine": "sqlite",
  "sqlite": {
    "database_path": "./reliability_test.db"
  }
}
```

> If no credentials are specified, the adapter will default to SQLite with a database file at `./reliability_test.db`
