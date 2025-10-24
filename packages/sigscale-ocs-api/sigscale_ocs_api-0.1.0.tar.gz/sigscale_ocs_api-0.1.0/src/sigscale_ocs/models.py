"""
Data models for the Sigscale OCS API wrapper.
Core functionality only.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Amount:
    """Amount with units."""

    amount: str
    units: str


@dataclass
class ValidFor:
    """Validity period."""

    start_date_time: Optional[str] = None
    end_date_time: Optional[str] = None


@dataclass
class ProductRef:
    """Product reference."""

    id: str
    href: Optional[str] = None


@dataclass
class Bucket:
    """Balance bucket entity."""

    id: str
    href: Optional[str] = None
    remained_amount: Optional[Amount] = None
    valid_for: Optional[ValidFor] = None
    product: Optional[ProductRef] = None
    # Legacy fields for backward compatibility
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    units: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: Optional[str] = None


@dataclass
class BalanceAdjustment:
    """Balance adjustment request."""

    product_id: str
    amount: float
    units: str = "cents"
    description: Optional[str] = None
