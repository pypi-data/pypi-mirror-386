"""
Product Catalog Management API (TMF620) for managing offerings.
"""

from typing import Dict, Any, Optional
from .client import OCSClient

# No specific models needed for core functionality


class ProductCatalog:
    """Product Catalog Management API client for TMF620."""

    def __init__(self, client: OCSClient):
        """
        Initialize Product Catalog client.

        Args:
            client: OCSClient instance
        """
        self.client = client
        self.base_endpoint = "/productCatalogManagement/v2"

    def list_offerings(
        self,
        fields: Optional[str] = None,
        description: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all product offerings.

        Args:
            fields: Attributes selection
            description: Filter by description
            lifecycle_status: Filter by lifecycle status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            price: Filter by price

        Returns:
            List of product offerings
        """
        params = {}
        if fields:
            params["fields"] = fields
        if description:
            params["description"] = description
        if lifecycle_status:
            params["lifecycleStatus"] = lifecycle_status
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if price:
            params["price"] = price

        return self.client.get(f"{self.base_endpoint}/productOffering", params=params)

    def create_offering(self, offering_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product offering.

        Args:
            offering_data: Product offering data

        Returns:
            Created offering data
        """
        return self.client.post(f"{self.base_endpoint}/productOffering", offering_data)

    def delete_offering(self, offering_id: str) -> None:
        """
        Delete a product offering.

        Args:
            offering_id: ID of the offering to delete
        """
        self.client.delete(f"{self.base_endpoint}/productOffering/{offering_id}")

    def list_catalogs(self) -> Dict[str, Any]:
        """
        List all catalogs.

        Returns:
            List of catalogs
        """
        return self.client.get(f"{self.base_endpoint}/catalog")

    def list_categories(self) -> Dict[str, Any]:
        """
        List all categories.

        Returns:
            List of categories
        """
        return self.client.get(f"{self.base_endpoint}/category")

    def list_product_specifications(self) -> Dict[str, Any]:
        """
        List all product specifications.

        Returns:
            List of product specifications
        """
        return self.client.get(f"{self.base_endpoint}/productSpecification")
