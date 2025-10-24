"""
Product Inventory Management API (TMF637) for managing product subscriptions.
"""

from typing import Dict, Any, Optional
from .client import OCSClient


class ProductInventory:
    """Product Inventory Management API client for TMF637."""

    def __init__(self, client: OCSClient):
        """
        Initialize Product Inventory client.

        Args:
            client: OCSClient instance
        """
        self.client = client
        self.base_endpoint = "/productInventoryManagement/v2"

    def list_products(
        self,
        fields: Optional[str] = None,
        status: Optional[str] = None,
        product_offering_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all product subscriptions.

        Args:
            fields: Attributes selection
            status: Filter by status
            product_offering_id: Filter by product offering ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            List of product subscriptions
        """
        params = {}
        if fields:
            params["fields"] = fields
        if status:
            params["status"] = status
        if product_offering_id:
            params["productOffering.id"] = product_offering_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        return self.client.get(f"{self.base_endpoint}/product", params=params)

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product subscription by ID.

        Args:
            product_id: ID of the product to retrieve

        Returns:
            Product subscription data
        """
        return self.client.get(f"{self.base_endpoint}/product/{product_id}")

    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product subscription (data purchase).

        Args:
            product_data: Product subscription data

        Returns:
            Created product data

        Example:
            >>> product_data = {
            ...     "name": "Data Subscription",
            ...     "description": "1GB data plan subscription",
            ...     "productOffering": {"id": "offering-id"},
            ...     "status": "active"
            ... }
            >>> result = inventory.create_product(product_data)
        """
        return self.client.post(f"{self.base_endpoint}/product", product_data)

    def delete_product(self, product_id: str) -> None:
        """
        Delete a product subscription.

        Args:
            product_id: ID of the product to delete
        """
        self.client.delete(f"{self.base_endpoint}/product/{product_id}")
