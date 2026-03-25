"""
Security and core-flow integration tests using FastAPI TestClient, real PostgreSQL,
and real Clerk JWTs (TEST_ADMIN_TOKEN / TEST_CUSTOMER_TOKEN).

Endpoints covered:
- Public: GET /products
- Admin-only: DELETE /products/{id}, GET /orders
- Authenticated (any signed-in user): GET /cart/items, POST /cart/items
"""

from __future__ import annotations

import uuid

import pytest


class TestAuthentication:
    """Missing or invalid Bearer token → 401 on protected routes."""

    def test_cart_without_token_returns_401(self, client, no_headers):
        r = client.get("/cart/items", headers=no_headers)
        assert r.status_code == 401

    def test_cart_with_invalid_token_returns_401(self, client, invalid_headers):
        r = client.get("/cart/items", headers=invalid_headers)
        assert r.status_code == 401

    def test_orders_list_without_token_returns_401(self, client, no_headers):
        r = client.get("/orders", headers=no_headers)
        assert r.status_code == 401

    def test_orders_list_with_invalid_token_returns_401(self, client, invalid_headers):
        r = client.get("/orders", headers=invalid_headers)
        assert r.status_code == 401


class TestAuthorization:
    """Role checks: customer must not perform admin-only actions."""

    def test_customer_cannot_delete_product_returns_403(
        self, client, customer_headers
    ):
        r = client.delete(
            f"/products/{uuid.uuid4()}",
            headers=customer_headers,
        )
        assert r.status_code == 403

    def test_customer_cannot_list_all_orders_returns_403(
        self, client, customer_headers
    ):
        r = client.get("/orders", headers=customer_headers)
        assert r.status_code == 403

    def test_admin_can_list_orders_returns_200(self, client, admin_headers):
        r = client.get("/orders", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert "orders" in body

    def test_admin_can_delete_product_returns_204(
        self, client, admin_headers, customer_headers
    ):
        create = client.post(
            "/products/",
            headers=admin_headers,
            data={
                "name": "pytest RBAC delete",
                "price": "1.00",
                "stock_qty": "1",
            },
        )
        assert create.status_code == 201, create.text
        product_id = create.json()["id"]

        deny = client.delete(f"/products/{product_id}", headers=customer_headers)
        assert deny.status_code == 403

        ok = client.delete(f"/products/{product_id}", headers=admin_headers)
        assert ok.status_code == 204


class TestPublicAndCustomerFlows:
    """Public catalog and authenticated cart flows."""

    def test_list_products_public_no_auth_returns_200(self, client, no_headers):
        r = client.get("/products", params={"limit": 5}, headers=no_headers)
        assert r.status_code == 200

    def test_customer_can_add_to_cart_returns_201(self, client, customer_headers):
        listing = client.get("/products", params={"limit": 1})
        assert listing.status_code == 200
        data = listing.json()
        products = data["products"]
        assert len(products) >= 1, "Database needs at least one product for this test"
        pid = products[0]["id"]
        if isinstance(pid, str):
            product_id = pid
        else:
            product_id = str(pid)

        r = client.post(
            "/cart/items",
            headers=customer_headers,
            json={"product_id": product_id, "quantity": 1},
        )
        assert r.status_code == 201, r.text
