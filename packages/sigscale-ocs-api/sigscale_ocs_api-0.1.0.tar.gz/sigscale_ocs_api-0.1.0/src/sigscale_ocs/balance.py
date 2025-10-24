"""
Balance Management API (TMF654) for balance adjustments and bucket operations.
"""

from typing import Dict, Any, Optional
from .client import OCSClient

# No specific models needed for core functionality


class BalanceManagement:
    """Balance Management API client for TMF654."""

    def __init__(self, client: OCSClient):
        """
        Initialize Balance Management client.

        Args:
            client: OCSClient instance
        """
        self.client = client
        self.base_endpoint = "/balanceManagement/v1"

    def _parse_bucket_data(self, bucket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse bucket data from API response into a more usable format.

        Args:
            bucket_data: Raw bucket data from API

        Returns:
            Parsed bucket data with normalized field names
        """
        parsed = {
            "id": bucket_data.get("id"),
            "href": bucket_data.get("href"),
        }

        # Parse remained amount
        remained_amount = bucket_data.get("remainedAmount", {})
        if remained_amount:
            parsed["remaining_amount"] = remained_amount.get("amount")
            parsed["units"] = remained_amount.get("units")

        # Parse validity period
        valid_for = bucket_data.get("validFor", {})
        if valid_for:
            parsed["valid_from"] = valid_for.get("startDateTime")
            parsed["valid_until"] = valid_for.get("endDateTime")

        # Parse product reference
        product_ref = bucket_data.get("product", {})
        if product_ref:
            parsed["product_id"] = product_ref.get("id")
            parsed["product_href"] = product_ref.get("href")

        return parsed

    def format_balance_amount(self, amount: str, units: str) -> str:
        """
        Format balance amount for display.

        Args:
            amount: The amount string (e.g., "1000000000b", "99000")
            units: The units (e.g., "octets", "cents")

        Returns:
            Formatted balance string
        """
        if units == "octets":
            # Convert bytes to more readable format
            try:
                # Remove 'b' suffix if present
                clean_amount = amount.replace("b", "")
                bytes_value = int(clean_amount)

                if bytes_value >= 1024**3:  # GB
                    return f"{bytes_value / (1024**3):.2f} GB"
                elif bytes_value >= 1024**2:  # MB
                    return f"{bytes_value / (1024**2):.2f} MB"
                elif bytes_value >= 1024:  # KB
                    return f"{bytes_value / 1024:.2f} KB"
                else:
                    return f"{bytes_value} bytes"
            except (ValueError, TypeError):
                return f"{amount} {units}"

        elif units == "cents":
            # Convert cents to dollars
            try:
                cents = int(amount)
                dollars = cents / 100
                return f"${dollars:.2f}"
            except (ValueError, TypeError):
                return f"{amount} {units}"

        else:
            return f"{amount} {units}"

    def create_adjustment(
        self,
        product_id: str,
        amount: float,
        units: str = "cents",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a balance adjustment (top-up) for a product.

        Args:
            product_id: ID of the product to adjust balance for
            amount: Amount to add to balance
            units: Units for the amount (cents, bytes, seconds, etc.)
            description: Optional description for the adjustment

        Returns:
            API response data

        Example:
            >>> client = OCSClient()
            >>> balance = BalanceManagement(client)
            >>> result = balance.create_adjustment(
            ...     "1605455656771-64", 1000, "cents")
        """
        data = {
            "amount": {"units": units, "amount": amount},
            "product": {"id": product_id},
        }

        if description:
            data["description"] = description

        return self.client.post(f"{self.base_endpoint}/balanceAdjustment", data)

    def list_buckets(self, product_id: str, parse: bool = True) -> Dict[str, Any]:
        """
        List all balance buckets for a product.

        Args:
            product_id: ID of the product to get buckets for
            parse: Whether to parse the response data into normalized format

        Returns:
            Bucket data (parsed or raw based on parse parameter)
        """
        raw_buckets = self.client.get(
            f"{self.base_endpoint}/bucket", params={"product.id": product_id}
        )

        if parse and isinstance(raw_buckets, dict):
            # If the response contains a list of buckets, parse each one
            if "bucket" in raw_buckets and isinstance(raw_buckets["bucket"], list):
                parsed_buckets = []
                for bucket in raw_buckets["bucket"]:
                    parsed_buckets.append(self._parse_bucket_data(bucket))
                return {"bucket": parsed_buckets}
            else:
                # Single bucket response
                return self._parse_bucket_data(raw_buckets)
        else:
            return raw_buckets

    def get_bucket(self, bucket_id: str, parse: bool = True) -> Dict[str, Any]:
        """
        Get details of a specific bucket.

        Args:
            bucket_id: ID of the bucket to retrieve
            parse: Whether to parse the response data into normalized format

        Returns:
            Bucket data (parsed or raw based on parse parameter)
        """
        raw_bucket = self.client.get(f"{self.base_endpoint}/bucket/{bucket_id}")

        if parse:
            return self._parse_bucket_data(raw_bucket)
        else:
            return raw_bucket
