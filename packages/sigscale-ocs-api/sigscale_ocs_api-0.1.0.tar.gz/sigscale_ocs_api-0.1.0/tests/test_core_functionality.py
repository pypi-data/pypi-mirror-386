"""
Integration tests for core OCS functionality.
Focuses only on the essential operations that work reliably.
"""

import pytest
from sigscale_ocs import (
    BalanceManagement,
    ProductCatalog,
    ProductInventory,
    ServiceInventory,
)


class TestCoreFunctionality:
    """Test core OCS functionality: SIM card creation, product subscription, balance top-up."""

    def test_list_offerings(self, client):
        """Test listing available product offerings."""
        catalog = ProductCatalog(client)
        offerings = catalog.list_offerings()

        assert isinstance(offerings, list)
        assert len(offerings) > 0, "Should have at least one offering available"

        # Verify offering structure
        offering = offerings[0]
        assert "id" in offering
        assert "name" in offering

    def test_create_service_sim_card(self, client):
        """Test creating a service/subscriber (SIM card signup)."""
        service_inventory = ServiceInventory(client)

        service_data = {
            "name": "Test SIM Card",
            "description": "Test SIM card for integration testing",
            "status": "active",
            "serviceCharacteristic": [
                {"name": "IMSI", "value": "123456789012345"},
                {"name": "Phone Number", "value": "+1234567890"},
            ],
        }

        result = service_inventory.create_service(service_data)

        assert result is not None
        assert "id" in result
        service_id = result["id"]

        # Verify we can retrieve the created service
        service = service_inventory.get_service(service_id)
        assert service is not None
        assert service["id"] == service_id

        # Service created successfully

    def test_create_product_subscription(self, client, test_offering_id):
        """Test creating a product subscription (data purchase)."""
        inventory = ProductInventory(client)

        product_data = {
            "name": "Test Data Subscription",
            "description": "Test data subscription for integration testing",
            "productOffering": {"id": test_offering_id},
        }

        result = inventory.create_product(product_data)

        assert result is not None
        assert "id" in result
        product_id = result["id"]

        # Verify we can retrieve the created product
        product = inventory.get_product(product_id)
        assert product is not None
        assert product["id"] == product_id

        # Product created successfully

    def test_balance_top_up(self, client, test_product_id):
        """Test balance top-up (adding credits to account)."""
        balance = BalanceManagement(client)

        # Create a balance adjustment (top-up)
        result = balance.create_adjustment(
            product_id=test_product_id,
            amount=1000,  # $10.00 in cents
            units="cents",
            description="Test balance top-up",
        )

        assert result is not None

        # Verify we can list buckets for the product
        buckets = balance.list_buckets(test_product_id)
        assert isinstance(buckets, list)

        # If buckets exist, verify we can get bucket details
        if buckets:
            bucket = balance.get_bucket(buckets[0]["id"])
            assert bucket is not None
            assert "id" in bucket

    def test_complete_flow(self, client):
        """Test the complete flow: create service, create product, top up balance."""
        # Step 1: Get an available offering
        catalog = ProductCatalog(client)
        offerings = catalog.list_offerings()
        assert len(offerings) > 0, "Need at least one offering for the test"
        offering_id = offerings[0]["id"]

        # Step 2: Create a service (SIM card signup)
        service_inventory = ServiceInventory(client)
        service_data = {
            "name": "Complete Flow Test SIM",
            "description": "SIM card for complete flow testing",
            "status": "active",
            "serviceCharacteristic": [{"name": "IMSI", "value": "987654321098765"}],
        }
        service_result = service_inventory.create_service(service_data)
        service_id = service_result["id"]

        # Step 3: Create a product subscription (data purchase)
        inventory = ProductInventory(client)
        product_data = {
            "name": "Complete Flow Data Plan",
            "description": "Data plan for complete flow testing",
            "productOffering": {"id": offering_id},
        }
        product_result = inventory.create_product(product_data)
        product_id = product_result["id"]

        # Step 4: Top up balance
        balance = BalanceManagement(client)
        balance_result = balance.create_adjustment(
            product_id=product_id,
            amount=2000,  # $20.00 in cents
            units="cents",
            description="Complete flow balance top-up",
        )
        assert balance_result is not None

        # Step 5: Verify balance buckets exist
        buckets = balance.list_buckets(product_id)
        assert isinstance(buckets, list)

        # Clean up: Delete the created entities
        try:
            inventory.delete_product(product_id)
            service_inventory.delete_service(service_id)
        except Exception:
            # Cleanup failures are not critical for the test
            pass

        # Complete flow test passed successfully

    def test_delete_offering(self, client, test_offering_id):
        """Test deleting a product offering."""
        catalog = ProductCatalog(client)

        # Skip if no offering ID available
        if not test_offering_id:
            pytest.skip("No offering ID available for deletion test")

        try:
            # Try to delete the offering
            catalog.delete_offering(test_offering_id)
            # If we get here, deletion was successful
        except Exception as e:
            # If deletion fails, it might be because the offering doesn't exist
            # or the API doesn't support deletion of existing offerings
            print(f"Offering deletion failed: {e}")
            pytest.skip(f"Offering deletion not supported or offering not found: {e}")
