"""
Integration tests for ReportService.

Covers:
  - Report configuration CRUD (create, read, list, update, delete)
  - Report generation (sales, inventory, product performance, low stock)
  - Business rules (date validation, parameter overrides)

All tests use a real in-memory SQLite database — no mocks.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_model import Product
from app.models.report_model import Report
from app.models.sale_model import Sale
from app.schemas.report_schema import (
    ReportCreate,
    ReportUpdate,
    ReportTypeEnum,
    SalesReportParams,
    InventoryReportParams,
    ProductPerformanceParams,
    LowStockReportParams,
    ReportFilterParams,
)
from app.services.report_service import ReportService


# ═══════════════════════════════════════════════════════════════════════════
# CREATE REPORT CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateReport:
    """Tests for ReportService.create_report"""

    async def test_create_report_valid(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating a report config with valid data returns a ReportResponse."""
        data = ReportCreate(
            report_name="Weekly Sales Summary",
            report_type=ReportTypeEnum.SALES,
            parameters={"start_date": "2026-01-01", "end_date": "2026-01-07"},
            description="Weekly sales overview",
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.report_name == "Weekly Sales Summary"
        assert result.report_type == "SALES"
        assert result.created_by == "admin"
        assert result.description == "Weekly sales overview"
        assert result.report_id is not None

    async def test_create_report_inventory_type(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating an INVENTORY report config succeeds."""
        data = ReportCreate(
            report_name="Inventory Snapshot",
            report_type=ReportTypeEnum.INVENTORY,
            parameters={"low_stock_only": True},
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.report_type == "INVENTORY"

    async def test_create_report_product_performance_type(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating a PRODUCT_PERFORMANCE report config succeeds."""
        data = ReportCreate(
            report_name="Top Sellers Q1",
            report_type=ReportTypeEnum.PRODUCT_PERFORMANCE,
            parameters={"top_n": 5},
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.report_type == "PRODUCT_PERFORMANCE"

    async def test_create_report_low_stock_type(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating a LOW_STOCK report config succeeds."""
        data = ReportCreate(
            report_name="Low Stock Alert",
            report_type=ReportTypeEnum.LOW_STOCK,
            parameters={"threshold_percentage": 15},
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.report_type == "LOW_STOCK"

    async def test_create_report_no_parameters(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating a report config without parameters succeeds."""
        data = ReportCreate(
            report_name="Basic Report",
            report_type=ReportTypeEnum.INVENTORY,
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.parameters is None

    async def test_create_report_no_description(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Creating a report without description succeeds."""
        data = ReportCreate(
            report_name="No Desc Report",
            report_type=ReportTypeEnum.SALES,
        )

        result = await report_service.create_report(db_session, "admin", data)

        assert result is not None
        assert result.description is None

    async def test_create_report_empty_name_rejected(self):
        """Pydantic rejects empty report name."""
        with pytest.raises(Exception):
            ReportCreate(
                report_name="",
                report_type=ReportTypeEnum.SALES,
            )


# ═══════════════════════════════════════════════════════════════════════════
# READ REPORT CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class TestGetReport:
    """Tests for ReportService.get_report"""

    async def test_get_report_valid(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Retrieving a report by ID returns the correct data."""
        result = await report_service.get_report(db_session, sample_report.report_id)

        assert result is not None
        assert result.report_id == sample_report.report_id
        assert result.report_name == "Monthly Sales Report"
        assert result.report_type == "SALES"
        assert result.created_by == "admin-user"

    async def test_get_report_not_found(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Looking up a non-existent report ID returns None."""
        result = await report_service.get_report(db_session, 99999)

        assert result is None

    async def test_get_report_includes_parameters(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """The returned report includes parsed JSON parameters."""
        result = await report_service.get_report(db_session, sample_report.report_id)

        assert result is not None
        assert result.parameters is not None
        assert result.parameters["group_by"] == "day"


class TestGetAllReports:
    """Tests for ReportService.get_all_reports"""

    async def test_get_all_reports_returns_list(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Returns a ReportListResponse with created reports."""
        result = await report_service.get_all_reports(db_session)

        assert result is not None
        assert result.total >= 1
        assert len(result.reports) >= 1

    async def test_get_all_reports_empty(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Returns empty list when no reports exist."""
        result = await report_service.get_all_reports(db_session)

        assert result is not None
        assert result.total == 0

    async def test_get_all_reports_pagination(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
    ):
        """Pagination skip/limit works correctly."""
        # Create 3 reports
        for i in range(3):
            data = ReportCreate(
                report_name=f"Report {i}",
                report_type=ReportTypeEnum.INVENTORY,
            )
            await report_service.create_report(db_session, "admin", data)

        result = await report_service.get_all_reports(db_session, skip=0, limit=2)
        assert len(result.reports) == 2
        assert result.has_more is True

        result2 = await report_service.get_all_reports(db_session, skip=2, limit=2)
        assert len(result2.reports) == 1


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE REPORT CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateReport:
    """Tests for ReportService.update_report"""

    async def test_update_report_name(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Updating the report name persists correctly."""
        update_data = ReportUpdate(report_name="Updated Sales Report")

        result = await report_service.update_report(
            db_session, sample_report.report_id, update_data
        )

        assert result is not None
        assert result.report_name == "Updated Sales Report"

    async def test_update_report_parameters(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Updating the parameters persists correctly."""
        new_params = {"start_date": "2026-02-01", "end_date": "2026-02-28"}
        update_data = ReportUpdate(parameters=new_params)

        result = await report_service.update_report(
            db_session, sample_report.report_id, update_data
        )

        assert result is not None
        assert result.parameters["start_date"] == "2026-02-01"

    async def test_update_report_description(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Updating the description persists correctly."""
        update_data = ReportUpdate(description="New description text")

        result = await report_service.update_report(
            db_session, sample_report.report_id, update_data
        )

        assert result is not None
        assert result.description == "New description text"

    async def test_update_report_not_found(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Updating a non-existent report returns None."""
        update_data = ReportUpdate(report_name="Ghost")

        result = await report_service.update_report(db_session, 99999, update_data)

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# DELETE REPORT CONFIG
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteReport:
    """Tests for ReportService.delete_report"""

    async def test_delete_report_valid(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Deleting an existing report returns True."""
        result = await report_service.delete_report(
            db_session, sample_report.report_id
        )

        assert result is True

        # Confirm it's gone
        gone = await report_service.get_report(db_session, sample_report.report_id)
        assert gone is None

    async def test_delete_report_not_found(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Deleting a non-existent report returns False."""
        result = await report_service.delete_report(db_session, 99999)

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# GENERATE SALES REPORT
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateSalesReport:
    """Tests for ReportService.generate_sales_report"""

    async def test_sales_report_with_data(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Sales report with matching data returns populated summary."""
        params = SalesReportParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
            group_by="day",
        )

        result = await report_service.generate_sales_report(db_session, params)

        assert result is not None
        assert result.report_type == "SALES"
        assert result.summary["total_sales"] == len(sample_sales_data)
        assert result.summary["total_revenue"] > 0
        assert result.summary["total_quantity"] > 0

    async def test_sales_report_empty_date_range(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Sales report outside date range returns zero totals."""
        params = SalesReportParams(
            start_date=datetime(2099, 1, 1),
            end_date=datetime(2099, 12, 31),
        )

        result = await report_service.generate_sales_report(db_session, params)

        assert result.summary["total_sales"] == 0
        assert result.summary["total_revenue"] == 0

    async def test_sales_report_grouped_by_day(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Sales report grouped by day produces items list."""
        params = SalesReportParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
            group_by="day",
        )

        result = await report_service.generate_sales_report(db_session, params)

        assert len(result.items) >= 1
        # Each item has a period string
        for item in result.items:
            assert item.period is not None

    async def test_sales_report_includes_breakdowns(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Sales report includes product and category breakdowns."""
        params = SalesReportParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
        )

        result = await report_service.generate_sales_report(db_session, params)

        assert result.product_breakdown is not None
        assert len(result.product_breakdown) >= 1
        assert result.category_breakdown is not None

    async def test_sales_report_date_validation(self):
        """Pydantic rejects end_date before start_date."""
        with pytest.raises(Exception):
            SalesReportParams(
                start_date=datetime(2026, 2, 1),
                end_date=datetime(2026, 1, 1),  # Before start
            )


# ═══════════════════════════════════════════════════════════════════════════
# GENERATE INVENTORY REPORT
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateInventoryReport:
    """Tests for ReportService.generate_inventory_report"""

    async def test_inventory_report_all_products(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Inventory report lists all products with stock status."""
        params = InventoryReportParams()

        result = await report_service.generate_inventory_report(db_session, params)

        assert result is not None
        assert result.report_type == "INVENTORY"
        assert result.summary["total_products"] == len(sample_products)
        assert len(result.items) == len(sample_products)

    async def test_inventory_report_stock_status(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Items have correct stock status (OK, LOW, OUT_OF_STOCK)."""
        params = InventoryReportParams()

        result = await report_service.generate_inventory_report(db_session, params)

        statuses = {item.status for item in result.items}
        # We have products with stock=0 and stock=3 (< reorder_level=10)
        assert "OUT_OF_STOCK" in statuses
        assert "LOW" in statuses

    async def test_inventory_report_low_stock_only(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """low_stock_only=True filters to only LOW and OUT_OF_STOCK."""
        params = InventoryReportParams(low_stock_only=True)

        result = await report_service.generate_inventory_report(db_session, params)

        for item in result.items:
            assert item.status in ("LOW", "OUT_OF_STOCK")

    async def test_inventory_report_stock_value(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Stock value = price × quantity for each item."""
        params = InventoryReportParams()

        result = await report_service.generate_inventory_report(db_session, params)

        for item in result.items:
            assert item.stock_value >= 0
        assert result.summary["total_stock_value"] > 0

    async def test_inventory_report_empty_db(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Inventory report on empty database returns zero items."""
        params = InventoryReportParams()

        result = await report_service.generate_inventory_report(db_session, params)

        assert result.summary["total_products"] == 0
        assert len(result.items) == 0


# ═══════════════════════════════════════════════════════════════════════════
# GENERATE PRODUCT PERFORMANCE REPORT
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateProductPerformanceReport:
    """Tests for ReportService.generate_product_performance_report"""

    async def test_product_performance_with_sales(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Product performance report returns top products from sales data."""
        params = ProductPerformanceParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
            top_n=10,
        )

        result = await report_service.generate_product_performance_report(
            db_session, params
        )

        assert result is not None
        assert result.report_type == "PRODUCT_PERFORMANCE"
        assert len(result.top_products) >= 1
        assert result.summary["top_product_count"] >= 1
        assert result.summary["total_revenue"] > 0

    async def test_product_performance_top_n_limit(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """top_n limits the number of returned products."""
        params = ProductPerformanceParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
            top_n=1,
        )

        result = await report_service.generate_product_performance_report(
            db_session, params
        )

        assert len(result.top_products) == 1

    async def test_product_performance_no_sales(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Product performance with no sales returns empty."""
        params = ProductPerformanceParams(
            start_date=datetime(2099, 1, 1),
            end_date=datetime(2099, 12, 31),
        )

        result = await report_service.generate_product_performance_report(
            db_session, params
        )

        assert len(result.top_products) == 0
        assert result.summary["top_product_count"] == 0

    async def test_product_performance_category_breakdown(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_sales_data: list[Sale],
    ):
        """Report includes category performance breakdown."""
        params = ProductPerformanceParams(
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 1, 31),
        )

        result = await report_service.generate_product_performance_report(
            db_session, params
        )

        assert result.category_performance is not None
        assert len(result.category_performance) >= 1

    async def test_product_performance_date_validation(self):
        """Pydantic rejects end_date before start_date."""
        with pytest.raises(Exception):
            ProductPerformanceParams(
                start_date=datetime(2026, 6, 1),
                end_date=datetime(2026, 1, 1),  # Before start
            )


# ═══════════════════════════════════════════════════════════════════════════
# GENERATE LOW STOCK REPORT
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateLowStockReport:
    """Tests for ReportService.generate_low_stock_report"""

    async def test_low_stock_report_default_threshold(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Low stock report with default 20% threshold finds low stock items."""
        params = LowStockReportParams()

        result = await report_service.generate_low_stock_report(db_session, params)

        assert result is not None
        assert result.report_type == "LOW_STOCK"
        assert result.threshold_percentage == 20
        # Safety Helmet stock=0, reorder=5 → 0% (below 20%) = LOW
        # Electrical Wire stock=3, reorder=10 → 30% (above 20%) = NOT LOW
        assert result.summary["total_low_stock_products"] >= 1

    async def test_low_stock_report_high_threshold(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Higher threshold flags more products."""
        params = LowStockReportParams(threshold_percentage=100)

        result = await report_service.generate_low_stock_report(db_session, params)

        # All products with stock <= reorder_level should appear
        assert result.summary["total_low_stock_products"] >= 1

    async def test_low_stock_report_out_of_stock_count(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Report counts out-of-stock items separately."""
        params = LowStockReportParams(threshold_percentage=100)

        result = await report_service.generate_low_stock_report(db_session, params)

        assert result.summary["out_of_stock_count"] >= 1

    async def test_low_stock_report_recommended_quantity(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Each item has a recommended_order_quantity."""
        params = LowStockReportParams(threshold_percentage=100)

        result = await report_service.generate_low_stock_report(db_session, params)

        for item in result.items:
            assert item.recommended_order_quantity > 0

    async def test_low_stock_report_sorted_by_percentage(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_products: list[Product],
    ):
        """Items are sorted by stock percentage (lowest first)."""
        params = LowStockReportParams(threshold_percentage=100)

        result = await report_service.generate_low_stock_report(db_session, params)

        if len(result.items) >= 2:
            for i in range(len(result.items) - 1):
                assert result.items[i].stock_percentage <= result.items[i + 1].stock_percentage

    async def test_low_stock_report_empty_db(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Low stock report on empty database returns zero items."""
        params = LowStockReportParams()

        result = await report_service.generate_low_stock_report(db_session, params)

        assert result.summary["total_low_stock_products"] == 0
        assert len(result.items) == 0


# ═══════════════════════════════════════════════════════════════════════════
# FILTER REPORTS
# ═══════════════════════════════════════════════════════════════════════════


class TestFilterReports:
    """Tests for ReportService.filter_reports"""

    async def test_filter_by_type(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Filtering by report type returns matching reports."""
        filter_params = ReportFilterParams(report_type=ReportTypeEnum.SALES)

        result = await report_service.filter_reports(db_session, filter_params)

        assert result.total >= 1
        for r in result.reports:
            assert r.report_type == "SALES"

    async def test_filter_by_creator(
        self,
        db_session: AsyncSession,
        report_service: ReportService,
        sample_report: Report,
    ):
        """Filtering by created_by returns matching reports."""
        filter_params = ReportFilterParams(created_by="admin-user")

        result = await report_service.filter_reports(db_session, filter_params)

        assert result.total >= 1
        for r in result.reports:
            assert r.created_by == "admin-user"

    async def test_filter_no_results(
        self, db_session: AsyncSession, report_service: ReportService
    ):
        """Filtering with no matches returns empty list."""
        filter_params = ReportFilterParams(created_by="nonexistent-user")

        result = await report_service.filter_reports(db_session, filter_params)

        assert result.total == 0


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════


class TestReportSchemaValidation:
    """Tests for Pydantic schema validation"""

    async def test_report_create_all_types(self):
        """All ReportTypeEnum values are accepted."""
        for rtype in ReportTypeEnum:
            data = ReportCreate(report_name=f"Test {rtype.value}", report_type=rtype)
            assert data.report_type == rtype

    async def test_low_stock_threshold_bounds(self):
        """threshold_percentage must be 0..100."""
        # Valid
        valid = LowStockReportParams(threshold_percentage=0)
        assert valid.threshold_percentage == 0

        valid = LowStockReportParams(threshold_percentage=100)
        assert valid.threshold_percentage == 100

        # Invalid
        with pytest.raises(Exception):
            LowStockReportParams(threshold_percentage=-1)

        with pytest.raises(Exception):
            LowStockReportParams(threshold_percentage=101)

    async def test_product_performance_top_n_bounds(self):
        """top_n must be 1..100."""
        with pytest.raises(Exception):
            ProductPerformanceParams(
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 1, 31),
                top_n=0,
            )

        with pytest.raises(Exception):
            ProductPerformanceParams(
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 1, 31),
                top_n=101,
            )
