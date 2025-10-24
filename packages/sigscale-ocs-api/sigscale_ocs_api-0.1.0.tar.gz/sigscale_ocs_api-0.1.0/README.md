# Sigscale OCS Python API Wrapper

A Python wrapper for the Sigscale OCS API supporting user signup, data purchases, balance top-ups, and offering management.

## Features

- **User Signup** - Add subscribers/services for SIM cards (TMF638)
- **Data Purchase** - Create product subscriptions (TMF637)
- **Balance Top-Up** - Add credits/data to user accounts (TMF654)
- **Offering Management** - Admin creates/manages product offerings (TMF620)
- Type-safe with dataclasses and comprehensive type hints
- Specific exception classes for better error handling
- SSL verification control for self-signed certificates
- Real integration tests against live API
- Automated PyPI publishing on releases

## Installation

```bash
pip install sigscale-ocs-api
```

## Configuration

Create a `.env` file with your OCS credentials:

```env
SIGSCALE_OCS_URL=https://ocs-build.sigscale.org:8096
SIGSCALE_OCS_USERNAME=admin
SIGSCALE_OCS_PASSWORD=admin
SIGSCALE_OCS_VERIFY_SSL=false
```

## Quick Start

### Core Operations (Recommended)

For the essential operations, use the focused example:

```bash
# Make sure you have the package installed
pip install -e .

# Test the package (no API connection required)
python test_import.py

# Run the core operations example (SIM card creation, data purchase, balance top-up)
python core_example.py
```

### Basic Usage

```python
from sigscale_ocs import OCSClient, BalanceManagement, ProductCatalog, ProductInventory, ServiceInventory

# Initialize client
client = OCSClient()

# Or with explicit credentials
client = OCSClient(
    base_url="https://ocs-build.sigscale.org:8096",
    username="admin",
    password="admin",
    verify_ssl=False
)
```

### User Signup (Service Inventory)

```python
from sigscale_ocs import ServiceInventory

service_inventory = ServiceInventory(client)

# Create a new subscriber (user signup)
service_data = {
    "name": "John Doe",
    "description": "New subscriber",
    "status": "active",
    "serviceCharacteristic": [
        {"name": "IMSI", "value": "123456789012345"}
    ]
}

subscriber = service_inventory.create_service(service_data)
print(f"Created subscriber: {subscriber['id']}")
```

### Data Purchase (Product Inventory)

```python
from sigscale_ocs import ProductInventory

product_inventory = ProductInventory(client)

# Create a product subscription (data purchase)
product_data = {
    "name": "Data Subscription",
    "description": "1GB data plan subscription",
    "productOffering": {"id": "your-offering-id"}
}

subscription = product_inventory.create_product(product_data)
print(f"Created subscription: {subscription['id']}")
```

### Balance Top-Up

```python
from sigscale_ocs import BalanceManagement

balance = BalanceManagement(client)

# Top up balance for a product
result = balance.create_adjustment(
    product_id="1605455656771-64",
    amount=1000,  # $10.00 in cents
    units="cents",
    description="Balance top-up"
)
print(f"Balance adjustment: {result}")

# List buckets for a product
buckets = balance.list_buckets("1605455656771-64")
print(f"Product buckets: {buckets}")

# Format balance amounts for display
for bucket in buckets:
    amount = bucket.get('remaining_amount')
    units = bucket.get('units')
    if amount and units:
        formatted = balance.format_balance_amount(amount, units)
        print(f"Bucket {bucket['id']}: {formatted}")
```

### Offering Management (Admin)

```python
from sigscale_ocs import ProductCatalog

catalog = ProductCatalog(client)

# Create a new offering
offering_data = {
    "name": "Data Plan 1GB",
    "description": "1GB data plan",
    "isBundle": False,
    "productOfferingPrice": [
        {
            "id": "price-1",
            "name": "Monthly Price",
            "price": {
                "unit": "USD",
                "value": 29.99
            }
        }
    ]
}

offering = catalog.create_offering(offering_data)
print(f"Created offering: {offering['id']}")

# List all offerings
offerings = catalog.list_offerings()
print(f"Available offerings: {len(offerings)}")
```

## API Reference

### OCSClient

Base client for API interactions.

```python
client = OCSClient(
    base_url="https://ocs-build.sigscale.org:8096",
    username="admin",
    password="admin",
    verify_ssl=False
)
```

### BalanceManagement (TMF654)

Balance adjustments and bucket operations.

- `create_adjustment(product_id, amount, units='cents', description=None)`
- `list_buckets(product_id, parse=True)` - Get balance buckets (parsed by default)
- `get_bucket(bucket_id, parse=True)` - Get bucket details (parsed by default)
- `format_balance_amount(amount, units)` - Format amounts for display (e.g., "1000000000b octets" → "953.67 MB")

### ProductCatalog (TMF620)

Product offering management.

- `list_offerings(fields=None, description=None, lifecycle_status=None, start_date=None, end_date=None, price=None)`
- `create_offering(offering_data)` - Create new offerings (may have request format limitations)
- `delete_offering(offering_id)` - Delete offerings
- `list_catalogs()` - List catalogs
- `list_categories()` - List categories
- `list_product_specifications()` - List product specifications

### ProductInventory (TMF637)

Product subscription management.

- `list_products(fields=None, status=None, product_offering_id=None, start_date=None, end_date=None)`
- `get_product(product_id)`
- `create_product(product_data)`
- `delete_product(product_id)`

### ServiceInventory (TMF638)

Service/subscriber management.

- `list_services(fields=None, status=None, product_id=None, start_date=None, end_date=None)`
- `get_service(service_id)`
- `create_service(service_data)`
- `delete_service(service_id)`

## Error Handling

The wrapper provides specific exception classes for different error scenarios:

```python
from sigscale_ocs import OCSClient, AuthenticationError, BadRequestError, NotFoundError, ServerError

try:
    client = OCSClient()
    # API calls...
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except BadRequestError as e:
    print(f"Bad request: {e}")
except NotFoundError as e:
    print(f"Resource not found: {e}")
except ServerError as e:
    print(f"Server error: {e}")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/keeganwhite/sigscale-ocs-api.git
cd sigscale-ocs-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Running Tests

```bash
# Set up test credentials
export SIGSCALE_OCS_URL="https://ocs-build.sigscale.org:8096"
export SIGSCALE_OCS_USERNAME="admin"
export SIGSCALE_OCS_PASSWORD="admin"
export SIGSCALE_OCS_VERIFY_SSL="false"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=sigscale_ocs --cov-report=html
```

### Code Quality

```bash
# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Formatting
black src/ tests/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes and releases.

## License

This project is licensed under the GNU GPL 3.0 - see the [LICENSE](LICENSE) file for details.
