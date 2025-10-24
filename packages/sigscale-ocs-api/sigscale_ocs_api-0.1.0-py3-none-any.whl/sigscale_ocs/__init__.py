"""
Sigscale OCS Python API Wrapper

A Python wrapper for the Sigscale OCS API supporting user signup,
data purchases, balance top-ups, and offering management.
"""

from .client import OCSClient
from .exceptions import (
    OCSAPIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    ServerError,
)
from .balance import BalanceManagement
from .product_catalog import ProductCatalog
from .product_inventory import ProductInventory
from .service_inventory import ServiceInventory

__version__ = "0.1.0"
__all__ = [
    "OCSClient",
    "OCSAPIError",
    "AuthenticationError",
    "BadRequestError",
    "NotFoundError",
    "ServerError",
    "BalanceManagement",
    "ProductCatalog",
    "ProductInventory",
    "ServiceInventory",
]
