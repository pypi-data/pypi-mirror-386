"""
Service Inventory Management API (TMF638) for managing subscribers/services.
"""

from typing import Dict, Any, Optional
from .client import OCSClient


class ServiceInventory:
    """Service Inventory Management API client for TMF638."""

    def __init__(self, client: OCSClient):
        """
        Initialize Service Inventory client.

        Args:
            client: OCSClient instance
        """
        self.client = client
        self.base_endpoint = "/serviceInventoryManagement/v2"

    def list_services(
        self,
        fields: Optional[str] = None,
        status: Optional[str] = None,
        product_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all services/subscribers.

        Args:
            fields: Attributes selection
            status: Filter by status
            product_id: Filter by product ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            List of services/subscribers
        """
        params = {}
        if fields:
            params["fields"] = fields
        if status:
            params["status"] = status
        if product_id:
            params["product.id"] = product_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        return self.client.get(f"{self.base_endpoint}/service", params=params)

    def get_service(self, service_id: str) -> Dict[str, Any]:
        """
        Get a specific service/subscriber by ID.

        Args:
            service_id: ID of the service to retrieve

        Returns:
            Service/subscriber data
        """
        return self.client.get(f"{self.base_endpoint}/service/{service_id}")

    def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new service/subscriber (user signup).

        Args:
            service_data: Service/subscriber data

        Returns:
            Created service data

        Example:
            >>> service_data = {
            ...     "name": "John Doe",
            ...     "description": "New subscriber",
            ...     "product": {"id": "product-id"},
            ...     "status": "active",
            ...     "serviceCharacteristic": [
            ...         {"name": "IMSI", "value": "123456789012345"}
            ...     ]
            ... }
            >>> result = inventory.create_service(service_data)
        """
        return self.client.post(f"{self.base_endpoint}/service", service_data)

    def delete_service(self, service_id: str) -> None:
        """
        Delete a service/subscriber.

        Args:
            service_id: ID of the service to delete
        """
        self.client.delete(f"{self.base_endpoint}/service/{service_id}")
